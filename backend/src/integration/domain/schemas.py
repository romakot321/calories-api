from typing import Literal, Any, Optional
from enum import Enum

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    OUTPUT_TEXT = "output_text"
    STRUCTURED_DATA = "structured_data"
    OUTPUT_IMAGE = "output_image"


class OutputText(BaseModel):
    type: ContentType = Field(ContentType.OUTPUT_TEXT)
    text: str


class StructuredData(BaseModel):
    type: ContentType = Field(ContentType.STRUCTURED_DATA)
    value: dict[str, Any]


class OutputImage(BaseModel):
    type: ContentType = Field(ContentType.OUTPUT_IMAGE)
    image_url: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


ContentItem = OutputText | StructuredData | OutputImage


class MessageItem(BaseModel):
    id: Optional[str] = None
    type: Optional[str] = None
    role: Optional[str] = None
    content: list[ContentItem] = Field(default_factory=list)
    metadata: Optional[dict[str, Any]] = None


class Usage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class OpenaiResponse(BaseModel):
    id: Optional[str] = None
    object: Optional[str] = None
    created: Optional[int] = None
    model: Optional[str] = None
    input: Optional[list[dict[str, Any]]] = None
    output: Optional[list[MessageItem]] = None
    usage: Optional[Usage] = None
    status: Optional[str] = None
    raw: Optional[dict[str, Any]] = None

    model_config = {"extra": "allow"}
