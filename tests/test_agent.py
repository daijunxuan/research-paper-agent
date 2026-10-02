import threading
import time

import pytest

from paper_agent.agent import ResearchAgent
from paper_agent.config import Settings
from paper_agent.ingest import ingest_pages
from paper_agent.models import ResearchRequest


def wait(store, job_id):
    for _ in range(200):
        job = store.job(job_id)
        if job["status"] in ("complete", "failed"):
            return job
        time.sleep(0.01)
    raise AssertionError("Job did not finish")


def request_for(store):
    paper = ingest_pages(
        store, "A paper", ["Our method freezes pretrained weights and trains small matrices. " * 8]
    )
    return ResearchRequest(task="summarize", paper_ids=[paper["id"]])


def test_citation_repair_is_bounded_and_recorded(store, tmp_path):
    class Generator:
        def __init__(self):
            self.calls = 0

        def generate(self, request, evidence, draft=None):
            self.calls += 1
            return ("Weights are frozen." if not draft else "Weights are frozen [E1]."), {
                "seconds": 1,
                "cold_start": self.calls == 1,
            }

    generator = Generator()
    agent = ResearchAgent(store, Settings(data_dir=tmp_path), generator)
    job = wait(store, agent.submit(request_for(store))["job_id"])
    agent.pool.shutdown()
    assert job["status"] == "complete" and generator.calls == 2
    assert job["payload"]["usage"]["cold_start"]
    assert job["payload"]["usage"]["attempts"] == 2
    assert job["payload"]["usage"]["total_generation_seconds"] == 2


def test_two_invalid_drafts_fail_without_fallback(store, tmp_path):
    class Generator:
        def __init__(self):
            self.calls = 0

        def generate(self, *args, **kwargs):
            self.calls += 1
            return "Fabricated citation [E99].", {"seconds": 0}

    generator = Generator()
    agent = ResearchAgent(store, Settings(data_dir=tmp_path), generator)
    job = wait(store, agent.submit(request_for(store))["job_id"])
    agent.pool.shutdown()
    assert job["status"] == "failed" and generator.calls == 2
    assert "markdown" not in job["payload"]


def test_worker_queue_is_bounded(store, tmp_path):
    release = threading.Event()

    class Generator:
        def generate(self, *args, **kwargs):
            release.wait(timeout=5)
            return "Result [E1].", {"seconds": 0}

    agent = ResearchAgent(store, Settings(data_dir=tmp_path), Generator())
    request = request_for(store)
    try:
        for i in range(3):
            agent.submit(request.model_copy(update={"question": f"method {i}"}))
        with pytest.raises(RuntimeError, match="three"):
            agent.submit(request)
    finally:
        release.set()
        agent.pool.shutdown()
