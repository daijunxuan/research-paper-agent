"""Offline retrieval regression; labels are committed before scoring, not model-judged."""

import json
import tempfile
from importlib.resources import files
from pathlib import Path

from paper_agent.ingest import ingest_pages
from paper_agent.retrieval import retrieve
from paper_agent.store import Store

# (query, index of the original teaching note, relevant physical/logical page)
CASES = [
    ("frozen pretrained weights pair low rank matrices", 0, 1),
    ("rank 4 8 16 ablation", 0, 2),
    ("which layers receive low rank update", 0, 2),
    ("BM25 lexical passages identifiers page numbers", 1, 1),
    ("top k 2 4 8 context budget", 1, 2),
    ("unanswerable query abstain", 1, 2),
    ("device model revision prompt version", 2, 1),
    ("two column formulas tables scanned multilingual", 2, 2),
    ("irrelevant instructions tool authority shell", 2, 2),
]


def evaluate():
    notes = json.loads(files("paper_agent").joinpath("fixtures/demo.json").read_text())
    with tempfile.TemporaryDirectory() as directory:
        store = Store(Path(directory))
        ids = [ingest_pages(store, n["title"], n["pages"], "demo")["id"] for n in notes]
        chunks = store.chunks(ids)
        rows = []
        for query, index, page in CASES:
            retrieved = retrieve(chunks, query, k=3)
            ranks = [
                i
                for i, c in enumerate(retrieved, 1)
                if c["paper_id"] == ids[index] and c["page"] == page
            ]
            rank = min(ranks) if ranks else None
            rows.append(
                {"query": query, "relevant_note": index, "relevant_page": page, "rank_at_3": rank}
            )
        negative = retrieve(chunks, "volcanic magma seismology", k=3)
        return {
            "dataset": "9 queries / 3 original synthetic notes / 6 pages",
            "scope": "lexical retrieval regression, not scientific reasoning quality",
            "recall_at_3": sum(r["rank_at_3"] is not None for r in rows) / len(rows),
            "mrr_at_3": sum(1 / r["rank_at_3"] if r["rank_at_3"] else 0 for r in rows) / len(rows),
            "irrelevant_query_abstained": not negative,
            "cases": rows,
        }


if __name__ == "__main__":
    value = evaluate()
    print(json.dumps(value, indent=2))
    if value["recall_at_3"] < 0.8 or not value["irrelevant_query_abstained"]:
        raise SystemExit("Retrieval regression failed")
