import hashlib
import json
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from .generation import make_generator, validate_references
from .retrieval import research_evidence

PROMPT_VERSION = "1.7"


class ResearchAgent:
    """A bounded research workflow, not an unrestricted autonomous browser agent."""

    def __init__(self, store, settings, generator=None):
        self.store, self.settings = store, settings
        self.generator = generator or make_generator(settings)
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="research")
        self.capacity = threading.BoundedSemaphore(3)

    def submit(self, request):
        self.store.get_papers(request.paper_ids)
        if request.task == "compare" and len(request.paper_ids) < 2:
            raise ValueError("Choose at least two papers to compare")
        if request.task == "question" and not request.question.strip():
            raise ValueError("Enter a research question")
        settings = self.settings.model_dump(mode="json", exclude={"data_dir", "ollama_url"})
        # Ollama is configured by a tag, so a changed tag's weights require clearing old reports.
        key = hashlib.sha256(
            json.dumps([request.model_dump(), settings, PROMPT_VERSION], sort_keys=True).encode()
        ).hexdigest()
        cached = self.store.cached(key)
        if cached:
            return {"job_id": cached["id"], "cached": True}
        if not self.capacity.acquire(blocking=False):
            raise RuntimeError(
                "The local worker has three active/queued tasks. Wait for one to finish."
            )
        job_id = uuid.uuid4().hex
        self.store.save_job(
            job_id, key, "queued", {"stage": "Waiting for local worker", "trace": []}
        )
        self.pool.submit(self._run, job_id, key, request)
        return {"job_id": job_id, "cached": False}

    def _run(self, job_id, key, request):
        started = time.perf_counter()
        trace = []

        def step(name, detail):
            trace.append(
                {
                    "step": name,
                    "detail": detail,
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                }
            )
            self.store.save_job(job_id, key, "running", {"stage": name, "trace": trace})

        try:
            step(
                "Retrieve evidence",
                "Search each selected paper; keep page boundaries and provenance.",
            )
            evidence = research_evidence(self.store, request)
            if not evidence:
                raise ValueError(
                    "No matching evidence found. Try terms used in the paper or import more text."
                )
            step(
                "Read and synthesize",
                f"{len(evidence)} excerpts; {self.settings.provider} provider.",
            )
            text, usage = self.generator.generate(request, evidence)
            step(
                "Validate references",
                "Reject citation IDs that are absent from the retrieved evidence.",
            )
            attempts = [usage]
            try:
                validation = validate_references(text, evidence, request)
            except ValueError:
                step(
                    "Repair citations",
                    "One bounded revision; never silently fabricate reference links.",
                )
                text, usage = self.generator.generate(request, evidence, draft=text)
                attempts.append(usage)
                validation = validate_references(text, evidence, request)
            usage = {
                **usage,
                "attempts": len(attempts),
                "total_generation_seconds": round(sum(a.get("seconds", 0) for a in attempts), 3),
                "cold_start": any(a.get("cold_start", False) for a in attempts),
            }
            report = {
                "request": request.model_dump(),
                "markdown": text,
                "evidence": evidence,
                "validation": validation,
                "usage": usage,
                "trace": trace,
                "prompt_version": PROMPT_VERSION,
                "seconds": round(time.perf_counter() - started, 3),
                "warnings": [
                    p["warning"] for p in self.store.get_papers(request.paper_ids) if p["warning"]
                ],
            }
            if usage.get("token_limit_reached"):
                report["warnings"].append(
                    "Generation reached the token limit; the last section may be incomplete."
                )
            self.store.save_job(job_id, key, "complete", report)
        except Exception as exc:
            # Never report a provider failure as a successful extractive/model answer.
            self.store.save_job(job_id, key, "failed", {"error": str(exc)[:500], "trace": trace})
        finally:
            self.capacity.release()


def export_markdown(report):
    lines = ["# Papertrail research brief", report["markdown"]]
    if report.get("warnings"):
        lines.extend(["## Warnings", *[f"- {w}" for w in report["warnings"]]])
    lines.append("\n## Evidence ledger")
    for e in report["evidence"]:
        lines.append(
            f"### [{e['ref']}] {e['title']} — page {e['page']} ({e['kind']})\n\n{e['text']}"
        )
    lines += [
        "\n## Provenance",
        json.dumps(
            {
                "usage": report["usage"],
                "validation": report["validation"],
                "prompt_version": report["prompt_version"],
            },
            indent=2,
        ),
    ]
    return "\n\n".join(lines)
