import logging

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    SummaryRequest,
    SummaryResponse,
)
from app.services.chat_service import chat_service
from app.services.chunker import chunk_text
from app.services.retriever import retrieve_relevant_chunks
from app.services.session_store import get_session, purge_expired_sessions, set_session
from app.services.summarizer import summarizer_service
from app.services.transcriber import transcriber_service

router = APIRouter()
logger = logging.getLogger(__name__)

_requests_since_purge = 0
_PURGE_EVERY_N_REQUESTS = 50


def _maybe_purge_sessions() -> None:
    global _requests_since_purge
    _requests_since_purge += 1
    if _requests_since_purge >= _PURGE_EVERY_N_REQUESTS:
        removed = purge_expired_sessions()
        _requests_since_purge = 0
        if removed:
            logger.info("Purged %d expired sessions", removed)


def _parse_ai_output(raw: str) -> tuple[str, list[str]]:
    """Split Gemini output into summary text and bullet-point insights."""
    lines = raw.split("\n")

    insights = [
        line.strip("- *•").strip()
        for line in lines
        if line.strip().startswith(("-", "*", "•")) and line.strip("- *•").strip()
    ]

    # Summary = everything before the first bullet, joined back together
    non_bullet_lines = [
        line for line in lines if not line.strip().startswith(("-", "*", "•"))
    ]
    summary_text = "\n".join(non_bullet_lines).strip() or raw.strip()

    if not insights:
        logger.warning("No bullet-point insights parsed from AI response; returning empty list")

    return summary_text, insights


@router.post("/summarize", response_model=SummaryResponse)
async def handle_summary(payload: SummaryRequest):
    _maybe_purge_sessions()

    video_id = transcriber_service.extract_video_id(payload.url)
    title = transcriber_service.get_video_title(video_id)
    transcript = transcriber_service.get_transcript(payload.url)

    raw_ai_output = await summarizer_service.summarize(transcript)
    summary_text, insights = _parse_ai_output(raw_ai_output)

    chunks = chunk_text(transcript)
    set_session(video_id, {"title": title, "transcript": transcript, "chunks": chunks})
    logger.info("Stored session for %s with %d chunks", video_id, len(chunks))

    return {
        "video_id": video_id,
        "title": title,
        "summary": summary_text,
        "insights": insights,
    }


@router.post("/chat", response_model=ChatResponse)
async def handle_chat(payload: ChatRequest):
    _maybe_purge_sessions()

    session = get_session(payload.video_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Transcript session not found or expired. Please re-summarize the video.",
        )

    chunks = session.get("chunks", [])
    relevant_chunks = retrieve_relevant_chunks(chunks, payload.question, top_k=8)

    answer = await chat_service.answer_question(
        question=payload.question,
        context_chunks=relevant_chunks,
        history=payload.history,
    )

    source_excerpts = [
        chunk[:200].strip() + ("..." if len(chunk) > 200 else "")
        for chunk in relevant_chunks
    ]

    return {"answer": answer, "sources": source_excerpts}
