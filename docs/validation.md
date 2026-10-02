# Validation record

Validation date: 2026-10-01 (America/Los_Angeles). This record separates offline regression checks, live service calls, model generation, and human inspection. It does not claim automated scientific fact verification.

## Host and dependencies

- Apple M2, 8 GiB unified memory; macOS 13.3; Python 3.13.2.
- PyTorch 2.6.0, Transformers 4.51.3, Accelerate 1.6.0.
- FastAPI 0.142.2, pypdf 6.19.0, rank-bm25 0.2.2, httpx 0.28.1.
- Local model weights only; no paid inference API, API key, or remote paper-processing service was used.

## Offline correctness

`pytest -q`: **35 passed** on the native host. The optional tensor compatibility test skips when Torch is not installed, including the lightweight CI environment. One dependency deprecation warning concerns Starlette's test client using httpx; the tests themselves pass.

`ruff check .` and the JavaScript syntax check pass. Tests cover parsing limits, page provenance, overlapping chunks, duplicate imports, blank/encrypted PDFs, irrelevant-query abstention, per-paper retrieval, reference validation, multi-paper reference coverage, repetitive-output rejection, bounded repair, queue saturation, cached reports, Markdown export, arXiv identifier validation and cache reuse, and cross-origin write protection.

The committed [retrieval evaluation](../examples/retrieval-eval.json) reports:

| Metric | Measured value |
|---|---:|
| Recall@3 | 1.000 |
| MRR@3 | 1.000 |
| Unrelated query returns no evidence | Yes |

This is **nine lexical queries over six pages of three original synthetic notes**. Queries deliberately have known relevant pages. The dataset is small and easy; these values establish regression behavior, not general research-paper retrieval performance.

Reproduce it with `python scripts/evaluate_retrieval.py`.

## Live PDF and external retrieval

- Downloaded the public [LoRA PDF](https://arxiv.org/abs/2106.09685), parsed 26 physical pages into 104 chunks, and retained page/chunk provenance.
- Asked which weights remain frozen and which parameters are trained. The final answer must be inspected against the supplied passages; merely passing the reference check is insufficient.
- Queried the real arXiv API for `low rank adaptation`, received live paper metadata, and imported the LoRA abstract by ID. The imported document is explicitly labeled **abstract**, with an incomplete-evidence warning.
- Search metadata without copied abstracts is recorded in [arxiv-live.json](../examples/arxiv-live.json). arXiv results can change; they are not a frozen benchmark.
- An early query using unnecessarily quoted terms and an explicit relevance-sort parameter timed out on the live API. The final client sends simple keyword field queries and handles service failures explicitly.

## Model selection and observed failures

Initial Qwen2.5-0.5B trials produced uncited answers and sometimes repetitive prompt echoes. A dynamic INT8 variant also produced an unusable answer. Those configurations were not accepted as the final demonstration. The reference validator now rejects highly repetitive output as well as unknown IDs, and a comparison must cite every selected document.

Qwen3-0.6B with a shorter source-first prompt completed all four task types on CPU. Human review still found missing experiment ideas and imprecise comparison wording. This illustrates why passing source-ID checks cannot establish factual correctness or completeness.

The macOS 13 MPS path initially failed on integer `torch.isin`. A narrowly scoped compatibility context replaces only Transformers' token-membership helpers with broadcast equality during generation, then restores them. It is active only for MPS on macOS earlier than 14. Scalar, vector, matrix and empty-set membership are checked against `torch.isin`; the primitive operation also passes on the actual MPS device. A full 1.7B MPS run was stopped after roughly four minutes without a completed answer, so this is not the recommended or validated end-to-end profile on this host.

## Selected local-model runs

The final default is **Qwen3-1.7B, CPU dynamic INT8**, revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`, four CPU threads, seed 42, thinking disabled, and a 700-token output cap. The other modules remain FP32. All four selected runs completed source-ID validation; none reached its token cap.

| Task | Source | Generation seconds, including repair | Attempts | Final output tokens |
|---|---|---:|---:|---:|
| question | LoRA PDF | 133.7 | 1 | 178 |
| summarize | original synthetic teaching notes | 125.9 | 2 | 280 |
| compare | original synthetic teaching notes | 61.0 | 1 | 286 |
| ideas | original synthetic teaching notes | 136.8 | 2 | 372 |

These are single smoke runs, not aggregate performance measurements. The question run includes model loading and quantization; other selected runs use a warm model. Queue time is excluded. Summary/question/comparison use prompt v1.6; the final focused experiment run uses v1.7. Those first three task templates did not change in v1.7. The screenshot shows an earlier repeated summary with the same text and a different observed runtime.

The experiment request explicitly asks for rank and layer-selection ablations; it is not an unconstrained discovery task. Broad requests on synthetic notes sometimes produced scientifically meaningless ideas. The focused draft is more useful, but its 90%/50% and 10%/20% failure thresholds remain arbitrary model proposals, not calibrated or source-supported recommendations. A researcher must replace them with task-appropriate criteria.

See [machine-readable run records](../examples/local-live.json), [summary](../examples/summarize.md), [comparison](../examples/compare.md) and [focused experiment draft](../examples/ideas.md). These files retain the actual accepted model output.

## Human review findings

The reference check is intentionally weaker than factual evaluation. Human inspection of the live drafts found that the summary compressed a **pair of matrices** into a singular matrix, and some proposed evaluations were phrased as if already carried out. These are errors to correct during research review, even when the source IDs are valid.

An early experiment draft invented tiny training-token budgets and included unsupported `[C1]`/`[C2]` labels. The final prompt requests **pilot resource planning without invented numeric budgets**, and the validator rejects unknown letter-plus-number reference IDs, including C-style labels. Raw accepted model drafts are included in `examples/` for inspection, not as scientifically endorsed plans.

## Browser checks

The real localhost app was inspected at desktop and narrow mobile width. The mobile document width matched the viewport width with no horizontal overflow. Real arXiv result cards appeared with paper titles, authors, dates and original links. A generated overview was loaded from the real report cache. Clicking `[E2]` opened and highlighted the page-2 source passage. The browser downloaded a 3,704-character Markdown report containing the evidence ledger. The screenshot records that live state. Packaging was also checked: the built wheel includes the HTML, CSS, JavaScript and demo fixtures.

## Scope not validated

Docker image execution, CUDA, a live Ollama server, large/scanned PDFs, multilingual retrieval quality, adversarial model robustness and broad scientific entailment accuracy are not validated. There is no claimed production reliability, automatic experimental execution, or full-paper systematic review.
