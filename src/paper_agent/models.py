from typing import Literal

from pydantic import BaseModel, Field


class TextImport(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    text: str = Field(min_length=100, max_length=250000)
    source_url: str = Field(default="", max_length=500)


class ResearchRequest(BaseModel):
    task: Literal["summarize", "compare", "ideas", "question"]
    paper_ids: list[str] = Field(min_length=1, max_length=4)
    question: str = Field(default="", max_length=1000)
    language: Literal["English", "Chinese"] = "English"


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=180)
    limit: int = Field(default=5, ge=1, le=8)


class ArxivImport(BaseModel):
    arxiv_id: str = Field(min_length=4, max_length=40)
