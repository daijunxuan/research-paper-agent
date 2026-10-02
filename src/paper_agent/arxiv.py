import re
import threading
import time
import xml.etree.ElementTree as ET

import httpx

NS = {"atom": "http://www.w3.org/2005/Atom"}
ID_PATTERN = r"(?:\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?"


class ArxivClient:
    def __init__(self):
        self.lock = threading.Lock()
        self.last_request = 0.0
        self.cache = {}

    def query(self, params):
        key = tuple(sorted(params.items()))
        with self.lock:
            cached = self.cache.get(key)
            if cached and time.monotonic() - cached[0] < 900:
                return cached[1]
            delay = 3.1 - (time.monotonic() - self.last_request)
            if delay > 0:
                time.sleep(delay)
            self.last_request = time.monotonic()
            try:
                response = httpx.get(
                    "https://export.arxiv.org/api/query",
                    params=params,
                    headers={"User-Agent": "Papertrail/0.1 (local research workbench)"},
                    timeout=30,
                    follow_redirects=False,
                )
                response.raise_for_status()
                records = parse_feed(response.text)
            except (httpx.HTTPError, ET.ParseError) as exc:
                raise ValueError(
                    "arXiv search is temporarily unavailable or rate-limited. Try again later."
                ) from exc
            self.cache[key] = (time.monotonic(), records)
            return records

    def search(self, query, limit=5):
        words = re.findall(r"[\w-]+", query)[:15]
        if not words:
            raise ValueError("Enter a title or research keywords")
        query = " AND ".join(f"all:{word}" for word in words)
        return self.query({"search_query": query, "start": 0, "max_results": limit})

    def fetch(self, arxiv_id):
        if not re.fullmatch(ID_PATTERN, arxiv_id):
            raise ValueError("Enter an arXiv ID such as 2106.09685, not a URL")
        records = self.query({"id_list": arxiv_id})
        if not records:
            raise ValueError("No paper found for this arXiv ID")
        return records[0]


def parse_feed(xml):
    root = ET.fromstring(xml)
    records = []
    for entry in root.findall("atom:entry", NS):
        identifier = entry.findtext("atom:id", "", NS)
        arxiv_id = identifier.split("/abs/")[-1]
        if not re.fullmatch(ID_PATTERN, arxiv_id):
            continue
        records.append(
            {
                "arxiv_id": arxiv_id,
                "title": " ".join(entry.findtext("atom:title", "", NS).split()),
                "abstract": " ".join(entry.findtext("atom:summary", "", NS).split()),
                "authors": [
                    a.findtext("atom:name", "", NS) for a in entry.findall("atom:author", NS)
                ],
                "published": entry.findtext("atom:published", "", NS)[:10],
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
            }
        )
    return records
