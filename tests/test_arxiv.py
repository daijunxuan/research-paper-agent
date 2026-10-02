from paper_agent.arxiv import parse_feed


def test_feed_parses_only_valid_paper_ids():
    xml = """<feed xmlns="http://www.w3.org/2005/Atom">
    <entry><id>http://arxiv.org/abs/2106.09685v2</id><title>A paper\n title</title>
    <summary>Abstract here.</summary><author><name>A. Author</name></author>
    <published>2021-06-17T00:00:00Z</published></entry>
    <entry><id>http://arxiv.org/api/errors</id><title>Error</title></entry></feed>"""
    papers = parse_feed(xml)
    assert len(papers) == 1
    assert papers[0]["title"] == "A paper title"
    assert papers[0]["url"] == "https://arxiv.org/abs/2106.09685v2"


def test_invalid_id_cannot_trigger_network(monkeypatch):
    import pytest
    from paper_agent.arxiv import ArxivClient

    monkeypatch.setattr(
        "paper_agent.arxiv.httpx.get", lambda *a, **k: pytest.fail("network called")
    )
    with pytest.raises(ValueError, match="arXiv ID"):
        ArxivClient().fetch("http://127.0.0.1/private")


def test_identical_searches_use_cached_metadata(monkeypatch):
    import httpx
    from paper_agent.arxiv import ArxivClient

    calls = []

    def get(url, **kwargs):
        calls.append(kwargs["params"])
        return httpx.Response(
            200,
            request=httpx.Request("GET", url),
            text='<feed xmlns="http://www.w3.org/2005/Atom"/>',
        )

    monkeypatch.setattr("paper_agent.arxiv.httpx.get", get)
    client = ArxivClient()
    assert client.search("low rank adaptation", 3) == []
    assert client.search("low rank adaptation", 3) == []
    assert len(calls) == 1
