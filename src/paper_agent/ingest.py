import hashlib
import io
import re

from pypdf import PdfReader

from .store import now


def normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def chunk_pages(pages, paper_id, size=170, overlap=35):
    if not 0 <= overlap < size:
        raise ValueError("Overlap must be smaller than chunk size")
    result = []
    for page_number, text in enumerate(pages, 1):
        words = normalize(text).split()
        for offset in range(0, len(words), size - overlap):
            part = " ".join(words[offset : offset + size])
            if len(part) < 40:
                continue
            result.append(
                {"id": f"{paper_id}:p{page_number}:c{offset}", "page": page_number, "text": part}
            )
            if offset + size >= len(words):
                break
    return result


def ingest_pages(store, title, pages, kind="text", source_url=""):
    if not pages or len(pages) > 120 or sum(map(len, pages)) > 800000:
        raise ValueError("Paper must have 1–120 pages and at most 800,000 extracted characters")
    # Include source kind so an abstract can never masquerade as uploaded full text.
    fingerprint = kind + "\n" + "\n".join(normalize(p) for p in pages)
    paper_id = hashlib.sha256(fingerprint.encode()).hexdigest()[:16]
    chunks = chunk_pages(pages, paper_id)
    if not chunks:
        raise ValueError("No usable text found. Scanned PDFs need OCR before importing.")
    warning = (
        "Abstract only: full methods and experiments are not available."
        if kind == "abstract"
        else ""
    )
    empty_pages = sum(len(normalize(p)) < 40 for p in pages)
    if empty_pages:
        warning += (
            f" {empty_pages} page(s) had little/no extractable text; inspect the original PDF."
        )
    paper = {
        "id": paper_id,
        "title": title.strip()[:200],
        "kind": kind,
        "source_url": source_url,
        "pages": len(pages),
        "created_at": now(),
        "warning": warning.strip(),
    }
    value, duplicate = store.add_paper(paper, chunks)
    return {**value, "duplicate": duplicate, "chunk_count": len(chunks)}


def ingest_pdf(store, data, filename, title=""):
    if not data.startswith(b"%PDF-"):
        raise ValueError("This file is not a PDF")
    try:
        reader = PdfReader(io.BytesIO(data), strict=False)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs are not supported; export an unlocked copy")
        if len(reader.pages) > 120:
            raise ValueError("Maximum PDF length is 120 pages")
        pages = []
        total = 0
        for page in reader.pages:
            value = page.extract_text() or ""
            total += len(value)
            if total > 800000:
                raise ValueError("Extracted PDF text exceeds the size limit")
            pages.append(value)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Could not parse this PDF. Try exporting a text-based PDF.") from exc
    return ingest_pages(store, title or filename.removesuffix(".pdf"), pages, "pdf")
