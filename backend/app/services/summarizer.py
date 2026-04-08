import asyncio
import logging

from fastapi import HTTPException
from google import genai

from app.core.config import settings

logger = logging.getLogger(__name__)


class SummarizerService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.model_id = "gemini-1.5-flash"

    async def summarize(self, transcript: str) -> str:
        if not transcript:
            raise HTTPException(status_code=400, detail="Transcript is empty")

        prompt = (
            "You are a professional multi-lingual content analyst. "
            "The following transcript might be in English, Filipino, or another language. "
            "Please translate the meaning and provide a concise summary IN ENGLISH, "
            "followed by a bulleted list of 3-5 key insights IN ENGLISH. "
            "Use Markdown formatting.\n\n"
            f"Transcript: {transcript}"
        )

        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_id,
                contents=prompt,
            )

            if not response.text:
                raise ValueError("AI returned an empty response")

            return response.text

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Gemini summarization failed: %s", e, exc_info=True)
            raise HTTPException(
                status_code=502,
                detail="AI Summarization service failed. Check API quota or key.",
            )


summarizer_service = SummarizerService()
