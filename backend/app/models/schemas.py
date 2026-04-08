from pydantic import BaseModel, field_validator


class SummaryRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("URL cannot be empty")
        if "youtube.com" not in v and "youtu.be" not in v:
            raise ValueError("Must be a valid YouTube URL")
        return v


class SummaryResponse(BaseModel):
    video_id: str
    title: str
    summary: str
    insights: list[str]


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    video_id: str
    question: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
