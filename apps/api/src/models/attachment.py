from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class AttachmentInput(BaseModel):
    """폼 첨부 1건. 이미지는 data_url(base64 data URL)을 담아 보내 백엔드가 업로드한다.
    이미지가 아닌 파일은 data_url 없이 이름만(현재는 이름만 본문에 기록)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, alias_generator=to_camel)

    name: str
    data_url: str | None = None  # "data:image/png;base64,...."
