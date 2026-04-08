import time
from typing import Any

# Sessions expire after 2 hours of inactivity
SESSION_TTL_SECONDS = 7200

# Structure: { video_id: { "title": str, "transcript": str, "chunks": list, "created_at": float } }
video_sessions: dict[str, dict[str, Any]] = {}


def set_session(video_id: str, data: dict[str, Any]) -> None:
    video_sessions[video_id] = {**data, "created_at": time.time()}


def get_session(video_id: str) -> dict[str, Any] | None:
    session = video_sessions.get(video_id)
    if session is None:
        return None
    if time.time() - session["created_at"] > SESSION_TTL_SECONDS:
        del video_sessions[video_id]
        return None
    return session


def purge_expired_sessions() -> int:
    """Remove all sessions older than SESSION_TTL_SECONDS. Returns count removed."""
    now = time.time()
    expired = [
        vid for vid, s in video_sessions.items()
        if now - s["created_at"] > SESSION_TTL_SECONDS
    ]
    for vid in expired:
        del video_sessions[vid]
    return len(expired)
