import time


def completed(client, job_id):
    for _ in range(100):
        result = client.get(f"/api/jobs/{job_id}").json()
        if result["status"] in ("complete", "failed"):
            return result
        time.sleep(0.01)
    raise AssertionError("Test job did not finish")


def test_demo_to_report_to_export_and_cache(client):
    papers = client.post("/api/demo").json()
    assert len(papers) == 3
    request = {"task": "summarize", "paper_ids": [papers[0]["id"]]}
    submitted = client.post("/api/research", json=request)
    assert submitted.status_code == 202
    job = completed(client, submitted.json()["job_id"])
    assert job["status"] == "complete"
    assert job["payload"]["usage"]["provider"] == "evidence"
    export = client.get(f"/api/jobs/{job['id']}/export")
    assert export.status_code == 200 and "Evidence ledger" in export.text
    assert client.post("/api/research", json=request).json()["cached"]


def test_question_abstains_without_relevant_evidence(client):
    paper = client.post("/api/demo").json()[0]
    submitted = client.post(
        "/api/research",
        json={
            "task": "question",
            "paper_ids": [paper["id"]],
            "question": "penguin migration antarctica",
        },
    ).json()
    job = completed(client, submitted["job_id"])
    assert job["status"] == "failed"
    assert "No matching evidence" in job["payload"]["error"]


def test_compare_requires_two_papers(client):
    paper = client.post("/api/demo").json()[0]
    assert (
        client.post(
            "/api/research", json={"task": "compare", "paper_ids": [paper["id"]]}
        ).status_code
        == 400
    )


def test_paper_scope_cannot_escape_library(client):
    assert (
        client.post(
            "/api/research", json={"task": "summarize", "paper_ids": ["not-present"]}
        ).status_code
        == 400
    )


def test_cross_origin_write_rejected(client):
    assert client.post("/api/demo", headers={"Origin": "https://other.example"}).status_code == 403


def test_arxiv_import_rejects_arbitrary_urls(client):
    response = client.post("/api/papers/arxiv", json={"arxiv_id": "http://127.0.0.1/secret"})
    assert response.status_code == 400


def test_invalid_upload_rejected(client):
    assert client.post("/api/papers/pdf", files={"file": ("x.pdf", b"not pdf")}).status_code == 400


def test_empty_question_rejected(client):
    paper = client.post("/api/demo").json()[0]
    assert (
        client.post(
            "/api/research", json={"task": "question", "paper_ids": [paper["id"]]}
        ).status_code
        == 400
    )


def test_browser_assets_and_health(client):
    assert client.get("/").status_code == 200
    assert "papertrail" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/api/health").json()["provider"] == "evidence"
