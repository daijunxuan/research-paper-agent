import json
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .agent import ResearchAgent, export_markdown
from .arxiv import ArxivClient
from .config import Settings
from .ingest import ingest_pages, ingest_pdf
from .models import ArxivImport, ResearchRequest, SearchRequest, TextImport
from .store import Store

ROOT = Path(__file__).parent


def create_app(settings=None, generator=None):
    settings = settings or Settings()
    store = Store(settings.data_dir)
    agent = ResearchAgent(store, settings, generator)
    arxiv = ArxivClient()

    @asynccontextmanager
    async def lifespan(app):
        yield
        agent.pool.shutdown(wait=False, cancel_futures=True)

    app = FastAPI(title="Papertrail Research Agent", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "[::1]", "testserver"]
    )
    app.state.store, app.state.agent = store, agent

    @app.middleware("http")
    async def local_origin(request: Request, call_next):
        origin = request.headers.get("origin")
        if request.method not in ("GET", "HEAD", "OPTIONS") and origin:
            if urlparse(origin).netloc != request.url.netloc:
                return JSONResponse({"detail": "Cross-origin writes are disabled"}, status_code=403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'"
        )
        return response

    @app.exception_handler(ValueError)
    async def bad_request(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=400)

    @app.get("/api/health")
    def health():
        return {
            "status": "ok",
            "provider": settings.provider,
            "model": settings.model_id if settings.provider != "evidence" else None,
            "local_only": True,
            "papers": len(store.papers()),
        }

    @app.get("/api/papers")
    def papers():
        return store.papers()

    @app.post("/api/papers/text", status_code=201)
    def text_import(body: TextImport):
        if body.source_url and urlparse(body.source_url).scheme not in ("https", "http"):
            raise ValueError("Source URL must use http or https")
        return ingest_pages(store, body.title, body.text.split("\f"), source_url=body.source_url)

    @app.post("/api/papers/pdf", status_code=201)
    def pdf_import(file: UploadFile = File(...), title: str = Form("")):
        data = file.file.read(settings.max_upload_bytes + 1)
        if len(data) > settings.max_upload_bytes:
            raise HTTPException(413, "PDF exceeds the 20 MiB upload limit")
        return ingest_pdf(store, data, file.filename or "Untitled paper.pdf", title)

    @app.post("/api/demo", status_code=201)
    def demo():
        fixtures = json.loads((ROOT / "fixtures/demo.json").read_text())
        return [ingest_pages(store, p["title"], p["pages"], kind="demo") for p in fixtures]

    @app.post("/api/related")
    def related(body: SearchRequest):
        return {
            "provider": "arXiv",
            "scope": "metadata and abstracts",
            "papers": arxiv.search(body.query, body.limit),
        }

    @app.post("/api/papers/arxiv", status_code=201)
    def arxiv_import(body: ArxivImport):
        paper = arxiv.fetch(body.arxiv_id)
        return ingest_pages(store, paper["title"], [paper["abstract"]], "abstract", paper["url"])

    @app.post("/api/research", status_code=202)
    def research(body: ResearchRequest):
        try:
            return agent.submit(body)
        except RuntimeError as exc:
            raise HTTPException(429, str(exc)) from exc

    @app.get("/api/jobs/{job_id}")
    def job(job_id: str):
        value = store.job(job_id)
        if not value:
            raise HTTPException(404, "Analysis not found")
        return value

    @app.get("/api/jobs/{job_id}/export")
    def export(job_id: str):
        value = store.job(job_id)
        if not value or value["status"] != "complete":
            raise HTTPException(404, "Completed report not found")
        return Response(
            export_markdown(value["payload"]),
            media_type="text/markdown",
            headers={"Content-Disposition": 'attachment; filename="research-brief.md"'},
        )

    @app.get("/")
    def home():
        return FileResponse(ROOT / "static/index.html")

    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    return app
