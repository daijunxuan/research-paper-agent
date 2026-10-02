import io

import pytest
from pypdf import PdfWriter

from paper_agent.ingest import chunk_pages, ingest_pages, ingest_pdf


def test_chunking_preserves_page_boundaries():
    chunks = chunk_pages(["apple " * 400, "banana " * 220], "paper")
    assert {c["page"] for c in chunks} == {1, 2}
    assert all("banana" not in c["text"] for c in chunks if c["page"] == 1)
    assert max(len(c["text"].split()) for c in chunks) <= 170


def test_overlap_and_tail():
    chunks = chunk_pages([" ".join(f"term{i}" for i in range(230))], "paper")
    assert "term169" in chunks[0]["text"] and "term169" in chunks[1]["text"]
    assert "term229" in chunks[-1]["text"]


def test_deduplication_and_source_type(store):
    text = "The method freezes pretrained weights and adapts low rank matrices. " * 4
    first = ingest_pages(store, "Original", [text])
    duplicate = ingest_pages(store, "Renamed", [text])
    abstract = ingest_pages(store, "Abstract", [text], "abstract")
    assert duplicate["duplicate"] and first["id"] == duplicate["id"]
    assert abstract["id"] != first["id"] and "Abstract only" in abstract["warning"]
    assert len(store.papers()) == 2


def test_invalid_pdf_rejected(store):
    with pytest.raises(ValueError, match="not a PDF"):
        ingest_pdf(store, b"hello", "paper.pdf")


def test_blank_pdf_needs_ocr(store):
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    target = io.BytesIO()
    writer.write(target)
    with pytest.raises(ValueError, match="OCR"):
        ingest_pdf(store, target.getvalue(), "scan.pdf")


def test_encrypted_pdf_rejected(store):
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.encrypt("test")
    target = io.BytesIO()
    writer.write(target)
    with pytest.raises(ValueError, match="Encrypted"):
        ingest_pdf(store, target.getvalue(), "encrypted.pdf")


def test_partial_empty_page_warns(store):
    paper = ingest_pages(store, "Mixed", ["", "Enough extractable research method text. " * 8])
    assert "1 page(s)" in paper["warning"]
    assert {c["page"] for c in store.chunks([paper["id"]])} == {2}
