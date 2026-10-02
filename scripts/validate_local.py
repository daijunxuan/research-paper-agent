"""Opt-in live local-model check. Start papertrail first; no model is downloaded by this script."""

import argparse
import json
import time
from pathlib import Path

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, help="Optional text-based PDF to test real ingestion")
    parser.add_argument("--output", type=Path, default=Path(".data/live-validation"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    with httpx.Client(base_url="http://127.0.0.1:8765", timeout=60) as client:
        health = client.get("/api/health").json()
        if health["provider"] == "evidence":
            raise SystemExit("Start the local or Ollama provider to evaluate generation.")
        response = client.post("/api/demo", json={})
        response.raise_for_status()
        papers = response.json()
        ids = [p["id"] for p in papers]
        tasks = [("summarize", ids[:1]), ("compare", ids[:2]), ("ideas", ids[:1])]
        if args.pdf:
            with args.pdf.open("rb") as file:
                response = client.post("/api/papers/pdf", files={"file": (args.pdf.name, file)})
            response.raise_for_status()
            tasks.insert(0, ("summarize", [response.json()["id"]]))
        for index, (task, selected) in enumerate(tasks):
            response = client.post(
                "/api/research",
                json={"task": task, "paper_ids": selected, "question": "", "language": "English"},
            )
            response.raise_for_status()
            created = response.json()
            deadline = time.monotonic() + 1200
            while time.monotonic() < deadline:
                response = client.get("/api/jobs/" + created["job_id"])
                response.raise_for_status()
                job = response.json()
                if job["status"] in ("complete", "failed"):
                    break
                time.sleep(2)
            else:
                raise SystemExit("Timed out; inspect the still-running job in the application.")
            records.append(
                {
                    "task": task,
                    "status": job["status"],
                    "cached": created["cached"],
                    "usage": job["payload"].get("usage"),
                    "error": job["payload"].get("error"),
                }
            )
            (args.output / f"{index}-{task}.json").write_text(json.dumps(job, indent=2))
            if job["status"] == "complete":
                exported = client.get("/api/jobs/" + job["id"] + "/export")
                exported.raise_for_status()
                (args.output / f"{index}-{task}.md").write_text(exported.text)
            print(f"{task}: {job['status']}", flush=True)
    (args.output / "summary.json").write_text(
        json.dumps({"health": health, "runs": records}, indent=2)
    )
    if any(r["status"] != "complete" for r in records):
        raise SystemExit("Some model runs failed; inspect the saved reports.")
    print("Reference checks passed. Human review of factual support is still required.")


if __name__ == "__main__":
    main()
