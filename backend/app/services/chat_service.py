import asyncio
import logging

from fastapi import HTTPException

from app.models.schemas import ChatMessage
from app.services.summarizer import summarizer_service

logger = logging.getLogger(__name__)


class ChatService:
    async def answer_question(
        self,
        question: str,
        context_chunks: list[str],
        history: list[ChatMessage] | None = None,
    ) -> str:
        if not question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        if not context_chunks:
            raise HTTPException(status_code=404, detail="No transcript context found")

        history = history or []

        context = "\n\n".join(
            [f"[Segment {i + 1}]\n{chunk}" for i, chunk in enumerate(context_chunks)]
        )

        history_text = "\n".join([f"{m.role}: {m.content}" for m in history])

        prompt = (
            "You are a Senior Video Content Analyst. You are helping a user understand "
            "the nuances of a YouTube video based on its transcript.\n\n"
            "INSTRUCTIONS:\n"
            "1. ANALYZE SENTIMENT: If the user asks for advice or an outlook (e.g., 'should I buy?'), "
            "identify the speaker's stance, risks mentioned, and overall tone.\n"
            "2. BE NUANCED: If the speaker doesn't give a direct answer, summarize their "
            "related arguments so the user can draw their own conclusion.\n"
            "3. FALLBACK: Only say 'I couldn't find that' if the question is totally "
            "unrelated to the video topics.\n"
            "4. CONTEXT: Use the transcript below as your primary source of truth.\n\n"
            f"PREVIOUS CONVERSATION:\n{history_text}\n\n"
            f"VIDEO TRANSCRIPT SEGMENTS:\n{context}\n\n"
            f"USER QUESTION: {question}"
        )

        try:
            response = await asyncio.to_thread(
                summarizer_service.client.models.generate_content,
                model=summarizer_service.model_id,
                contents=prompt,
            )

            if not response.text:
                return "The AI was unable to generate a response for this segment."

            return response.text.strip()

        except Exception as e:
            logger.error("Chat generation failed: %s", e, exc_info=True)
            raise HTTPException(
                status_code=502,
                detail="AI chat service is currently unavailable.",
            )


chat_service = ChatService()
