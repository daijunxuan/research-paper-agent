# Architecture and design decisions

## Product boundary

Papertrail is a single-user research application. A selected set of documents scopes every retrieval and report. A task chooses one of four prompt templates (overview, comparison, experiment ideas, question), runs retrieval, invokes a local language model and checks the returned reference identifiers. Related-work discovery is a separate explicit arXiv request; it never sends the PDF or a full generated report to a search service.

This is a bounded RAG workflow rather than an autonomous, self-directed agent. Deterministic orchestration makes execution cost, privacy and failure behavior easier to inspect. It also avoids giving model output authority to execute code or follow instructions embedded in papers.

## Data model

SQLite stores `papers`, `chunks` and `jobs`. Transactions protect paper+chunk insertion. Foreign keys link chunks to papers; indexes serve document and report-cache lookups. Each document ID is the SHA-256 prefix of normalized extracted pages plus source kind. A PDF and an abstract with similar text remain distinct. Repeat imports are idempotent; the first imported title wins for identical content.

The parser keeps page boundaries before chunking. Every chunk has a stable document ID, physical page number, word offset and original extracted text. The request-specific E1/E2 labels map to these immutable chunks. Text notes use form-feed separators as logical page boundaries; abstracts are one logical page.

Jobs persist stage updates, model metadata, timing, output and evidence. On startup, unfinished jobs are marked failed instead of being shown as still running. The service supports one worker process only. Running multiple Uvicorn workers would create independent model copies and independent scheduling locks.

## Retrieval decisions

BM25Plus gives a transparent sparse baseline without an embedding download or vector service. Its additive score can be positive even with no matching terms, so candidates must have lexical overlap. Near-identical passages from the same page are suppressed. Comparison retrieval is performed per paper so one document cannot consume every evidence slot.

Generic overview/compare/idea tasks use fixed task queries when the user supplies no focus. If those generic searches find no lexical match, opening passages provide explicitly limited context. Specific questions abstain when no matching passages exist. Lexical overlap is only a weak relevance signal; thresholds, synonym expansion and dense retrieval are future evaluation choices, not guarantees in this version.

Context is bounded to a small evidence set and 6,000 input tokens in the local backend. Longer reports require more output tokens and can be truncated; that condition is surfaced in report warnings. The evidence set is visible to the user, so missing coverage can be inspected.

## Local generation and failure behavior

The model loads lazily and is reused by a single background worker. CPU inference quantizes linear layers dynamically to INT8; embeddings, normalization and other unquantized modules remain FP32. ARM uses QNNPACK. The default Qwen3-1.7B model runs with thinking disabled and a fixed sampling seed. Non-CPU profiles use FP16. The default model revision is pinned; offline execution works once model assets are cached.

Generated references are checked against the retrieved set. A failed first check triggers one revision request rebuilt from the same evidence and stricter reference instructions. After two invalid drafts, the task fails. There is no invisible fallback from a failed model to an extractive response. The intentionally separate evidence provider is labeled as non-generative throughout the UI.

Reference-ID validation is not entailment verification. The application does not claim that all factual sentences are grounded simply because at least one valid citation appears. Generated claims, experiment budgets and proposed improvements still require researcher review. The model has no tool access, and HTML is rendered as text nodes rather than executed.

## API

| Endpoint | Purpose |
|---|---|
| `POST /api/papers/pdf` | Multipart PDF ingestion |
| `POST /api/papers/text` | Original paper text/notes |
| `POST /api/related` | arXiv keyword search |
| `POST /api/papers/arxiv` | Import a verified arXiv abstract by ID |
| `POST /api/research` | Queue a bounded research job |
| `GET /api/jobs/{id}` | Poll progress/result |
| `GET /api/jobs/{id}/export` | Download report + evidence ledger |
| `POST /api/demo` | Import original synthetic fixtures |

## Security and operating assumptions

The CLI binds only to 127.0.0.1. Trusted-host checks and same-origin write checks reduce drive-by browser interaction. The frontend has a restrictive content security policy, no external scripts, no inline event handlers and no HTML insertion from model or PDF text. arXiv IDs are validated before requests to a fixed API endpoint; user-provided arbitrary URLs are never fetched.

PDF size, page count and extracted-text length are bounded. PDF parsing is not a hardened isolation sandbox; do not run the local application as an internet-facing upload service. Paper text and reports are plaintext in the local data directory. The application does not provide encryption at rest, user accounts or per-user permissions.

## Reproducibility

Prompt version and model configuration participate in the cache key. Results include generation time, provider/model identity, generated token count when available, whether the output limit was reached and how many generation attempts were required. The synthetic retrieval evaluation is reproducible without network access. Real arXiv results can change over time and are not treated as frozen evaluation labels.
