import logging
import os
import re

import requests
from fastapi import HTTPException
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled, YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig, GenericProxyConfig

logger = logging.getLogger(__name__)


def _build_proxy_config():
    """Return a proxy config if env vars are set, else None (works locally without proxy)."""
    webshare_user = os.getenv("WEBSHARE_PROXY_USERNAME")
    webshare_pass = os.getenv("WEBSHARE_PROXY_PASSWORD")
    if webshare_user and webshare_pass:
        logger.info("Using Webshare proxy for YouTube transcript requests")
        return WebshareProxyConfig(
            proxy_username=webshare_user,
            proxy_password=webshare_pass,
        )

    generic_proxy = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
    if generic_proxy:
        logger.info("Using generic proxy for YouTube transcript requests")
        return GenericProxyConfig(http=generic_proxy, https=generic_proxy)

    return None


class TranscriberService:
    @staticmethod
    def extract_video_id(url: str) -> str:
        pattern = r"(?:v=|\/|be\/)([0-9A-Za-z_-]{11})"
        match = re.search(pattern, url)
        if not match:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")
        return match.group(1)

    def get_video_title(self, video_id: str) -> str:
        try:
            oembed_url = f"https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v={video_id}&format=json"
            response = requests.get(oembed_url, timeout=5)
            response.raise_for_status()
            return response.json().get("title", "YouTube Video")
        except (requests.RequestException, ValueError, KeyError) as e:
            logger.warning("Could not fetch video title for %s: %s", video_id, e)
            return "YouTube Video"

    def get_transcript(self, url: str) -> str:
        video_id = self.extract_video_id(url)
        proxy_config = _build_proxy_config()
        api = YouTubeTranscriptApi(proxy_config=proxy_config) if proxy_config else YouTubeTranscriptApi()

        try:
            transcript_list = api.list(video_id)

            # Try English first, then any generated transcript, then first available
            try:
                transcript = transcript_list.find_transcript(["en"])
            except NoTranscriptFound:
                try:
                    transcript = transcript_list.find_generated_transcript(
                        [t.language_code for t in transcript_list]
                    )
                except NoTranscriptFound:
                    transcript = next(iter(transcript_list))

            data = transcript.fetch()
            full_text = [
                segment.text if hasattr(segment, "text") else segment["text"]
                for segment in data
            ]
            return " ".join(full_text)

        except (TranscriptsDisabled, NoTranscriptFound) as e:
            logger.warning("No captions available for video %s: %s", video_id, e)
            raise HTTPException(
                status_code=404,
                detail="Transcript unavailable: No captions found for this video.",
            )
        except StopIteration:
            logger.warning("Transcript list was empty for video %s", video_id)
            raise HTTPException(
                status_code=404,
                detail="Transcript unavailable: No captions found for this video.",
            )
        except Exception as e:
            logger.error("Unexpected error fetching transcript for %s: %s", video_id, e, exc_info=True)
            raise HTTPException(
                status_code=500,
                detail="An unexpected error occurred while fetching the transcript.",
            )


transcriber_service = TranscriberService()
