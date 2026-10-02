import math
import re
from collections import Counter

from rank_bm25 import BM25Plus

STOP = set("a an the is are of to and in for on with by from that this we as it be at or".split())


def tokenize(text):
    return [t for t in re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]", text.lower()) if t not in STOP]


def lexical_cosine(query, text):
    """Small secondary lexical scorer; explicitly not a neural embedding."""
    a, b = Counter(tokenize(query)), Counter(tokenize(text))
    denominator = math.sqrt(sum(x * x for x in a.values()) * sum(x * x for x in b.values()))
    return sum(v * b[k] for k, v in a.items()) / denominator if denominator else 0


def retrieve(chunks, query, k=6):
    if not chunks or not tokenize(query):
        return []
    tokens = [tokenize(c["text"]) for c in chunks]
    scores = BM25Plus(tokens).get_scores(tokenize(query))
    # BM25Plus adds a constant even for nonmatching documents: filter lexical overlap first.
    candidates = []
    for chunk, score, terms in zip(chunks, scores, tokens):
        if not set(tokenize(query)).intersection(terms):
            continue
        candidates.append(
            {**chunk, "score": float(score), "lexical_cosine": lexical_cosine(query, chunk["text"])}
        )
    candidates.sort(key=lambda c: (c["score"], c["lexical_cosine"]), reverse=True)
    # Avoid adjacent, mostly overlapping windows crowding out other evidence.
    result = []
    for c in candidates:
        if any(
            c["paper_id"] == r["paper_id"]
            and c["page"] == r["page"]
            and len(set(tokenize(c["text"])) & set(tokenize(r["text"])))
            / max(1, len(set(tokenize(c["text"])) | set(tokenize(r["text"]))))
            > 0.8
            for r in result
        ):
            continue
        result.append(c)
        if len(result) == k:
            break
    return result


TASK_QUERIES = {
    "summarize": "abstract contribution propose method approach experiments results limitations",
    "compare": "method architecture training parameters dataset evaluation accuracy memory limitations",
    "ideas": "limitations future work ablation training dataset evaluation robustness efficiency",
}


def research_evidence(store, request):
    papers = store.get_papers(request.paper_ids)
    query = request.question or TASK_QUERIES.get(request.task, "")
    chunks = store.chunks(request.paper_ids)
    result = []
    per_paper = max(2, 6 // len(papers))
    for paper in papers:
        subset = [c for c in chunks if c["paper_id"] == paper["id"]]
        selected = retrieve(subset, query, per_paper)
        # For structured overview tasks, include the opening context if vocabulary differs.
        if not selected and request.task != "question":
            selected = [{**c, "score": 0.0, "lexical_cosine": 0.0} for c in subset[:per_paper]]
        result.extend(selected)
    return [{**c, "ref": f"E{i}"} for i, c in enumerate(result, 1)]
