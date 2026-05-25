from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    cause_hypothesis: str = Field(min_length=1)
    reproduction_summary: str = Field(min_length=1)
    related_files: list[str] = Field(default_factory=list)
    developer_guide: str = Field(min_length=1)
    original_issue_url: HttpUrl
