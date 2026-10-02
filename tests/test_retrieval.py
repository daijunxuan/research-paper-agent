from paper_agent.ingest import ingest_pages
from paper_agent.models import ResearchRequest
from paper_agent.retrieval import research_evidence, retrieve


def test_retrieval_ranks_relevant_passage(store):
    a = ingest_pages(
        store, "Adaptation", ["Low rank matrix adaptation freezes pretrained weights. " * 8]
    )
    b = ingest_pages(
        store, "Retrieval", ["Passage retrieval uses BM25 indexing and citation evidence. " * 8]
    )
    results = retrieve(store.chunks([a["id"], b["id"]]), "BM25 passage retrieval")
    assert results[0]["paper_id"] == b["id"]


def test_unanswerable_query_returns_empty(store):
    a = ingest_pages(
        store, "Adaptation", ["Low rank matrix adaptation freezes pretrained weights. " * 8]
    )
    assert retrieve(store.chunks([a["id"]]), "penguin migration antarctica") == []


def test_compare_balances_papers(store):
    ids = [
        ingest_pages(store, str(i), [(f"Paper {i} method evaluation. " * 90)])["id"]
        for i in range(3)
    ]
    evidence = research_evidence(store, ResearchRequest(task="compare", paper_ids=ids))
    assert {e["paper_id"] for e in evidence} == set(ids)
    assert len({e["ref"] for e in evidence}) == len(evidence)
