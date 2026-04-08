# YouTube AI Transcriber - AI Coding Agent Instructions

## Project Overview
This is a **YouTube video transcription and AI summarization tool** with a React frontend and FastAPI backend. The system extracts YouTube transcripts in any language and generates English summaries with key insights using Google's Gemini API.

**Architecture**: Frontend (React + Vite + Tailwind) → Backend (FastAPI) → YouTube Transcript API + Google Gemini

---

## Critical Data Flow
1. User enters YouTube URL → Frontend sends to `POST /api/v1/summarize`
2. Backend extracts video ID via regex, fetches transcript (with language fallback), gets video title via oEmbed
3. Gemini API summarizes transcript → Response split into summary text + bulleted insights
4. Frontend displays title, summary paragraph, and 3-5 key takeaways in a styled card layout

**Key File References**:
- Response pipeline: [backend/app/api/routes.py](backend/app/api/routes.py#L8-L25)
- Frontend form/results: [frontend/src/App.jsx](frontend/src/App.jsx)

---

## Backend Services (FastAPI)

### TranscriberService ([backend/app/services/transcriber.py](backend/app/services/transcriber.py))
- **URL Extraction**: `extract_video_id()` uses regex pattern `(?:v=|\/|be\/)([0-9A-Za-z_-]{11})` to handle youtube.com, youtu.be, and embed formats
- **Title Fetching**: Calls YouTube oEmbed API (not authenticated) - gracefully falls back to "YouTube Video"
- **Transcript Fetching**: Critical multi-language fallback logic:
  1. Tries English transcript first
  2. Falls back to any auto-generated transcript (e.g., Filipino)
  3. Last resort: grabs first available transcript
- **Note**: Returns plain text (space-joined segments), not JSON

### SummarizerService ([backend/app/services/summarizer.py](backend/app/services/summarizer.py))
- **Model**: Gemini 2.5 Flash (fast, cost-effective)
- **Sync API Call**: Uses synchronous `client.models.generate_content()` inside async function (acceptable for flash model's speed)
- **Prompt Strategy**: Instructs model to:
  - Handle multiple languages in input
  - Always output in English
  - Use Markdown formatting with bullet points
- **Error Handling**: Returns 502 if API fails (quota/key issues)
- **Singleton Pattern**: Single instance (`summarizer_service`) instantiated at module level

### Configuration ([backend/app/core/config.py](backend/app/core/config.py))
- **Required Env**: `GOOGLE_API_KEY` (via `.env` file using pydantic-settings)
- **API Prefix**: `/api/v1`

---

## Frontend Architecture (React + Vite + Tailwind)

### App Component ([frontend/src/App.jsx](frontend/src/App.jsx))
- **State**: `url` (input), `data` (summary response), `loading`, `error`
- **Single POST Endpoint**: Calls `getSummary(url)` from [frontend/src/api.js](frontend/src/api.js)
- **Response Mapping**: Expects `{ video_id, title, summary, insights: [string] }`
- **UI Components**:
  - Header with red YouTube icon
  - Form with URL input + animated submit button (Sparkles/Spinner icons)
  - Results card showing title + summary paragraph
  - Blue section with Brain icon showing 3-5 key insights as numbered list
- **Animations**: Framer Motion fade-in on results (default presets)
- **Error Display**: Shows `err.response?.data?.detail` or default "Make sure backend is running!"

### API Module ([frontend/src/api.js](frontend/src/api.js))
- **Base URL**: `http://127.0.0.1:8000/api/v1` (hardcoded for dev - needs env var in production)
- **Single Method**: `getSummary(url)` → POST `/summarize` with `{ url }`
- **Library**: Axios instance (configured once, reused)

### Styling
- **Framework**: Tailwind CSS v4.2 + Tailwind's Vite plugin (not PostCSS build)
- **Design Style**: Modern gradient buttons, rounded shadows, responsive grid
- **Icons**: Lucide React (small, tree-shakeable library)

---

## Data Models

### Request ([backend/app/models/schemas.py](backend/app/models/schemas.py))
```python
class SummaryRequest(BaseModel):
    url: str  # Validated as string, not enforced URL format
```

### Response
```python
class SummaryResponse(BaseModel):
    video_id: str      # 11-char alphanumeric ID
    title: str         # From YouTube oEmbed or fallback
    summary: str       # First line of Gemini response
    insights: list[str]  # Stripped bullet points (-, *, •)
```

---

## Setup & Development Workflow

### Backend Setup
```bash
cd backend
pip install -r requirements.txt  # Assumed (not shown in repo)
# Create .env file with: GOOGLE_API_KEY=your_key
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev      # Starts Vite dev server on http://localhost:5173
npm run build    # Production bundle
npm run lint     # ESLint check
```

### Environment Variables
- **Backend**: `.env` file in project root with `GOOGLE_API_KEY`
- **Frontend**: Hardcoded `baseURL` in [frontend/src/api.js](frontend/src/api.js) (not env-driven)

---

## Common Patterns & Conventions

### Error Handling
- **Backend**: FastAPI HTTPException for validation (400) and service failures (502)
- **Frontend**: Catch axios response errors and display user-friendly messages

### Response Parsing
- Gemini returns raw Markdown text → [backend/app/api/routes.py](backend/app/api/routes.py#L19-L21) parses:
  - First non-empty line = summary
  - Lines starting with `-`, `*`, `•` = insights (cleaned of markers)
- This assumes Gemini follows the prompt structure; no JSON parsing

### URL Validation
- Frontend: HTML5 `type="url"` (basic client check)
- Backend: Regex validation in `extract_video_id()` (400 error if invalid format)

### CORS Configuration
- Hardcoded `allow_origins=["*"]` in [backend/app/main.py](backend/app/main.py#L9) for dev
- **Production**: Replace with specific frontend URL

---

## Extension Points

### Adding Features
- **New Video Processor**: Add method to TranscriberService (e.g., `get_captions()`, `get_duration()`)
- **New Summarization Option**: Extend SummarizerService (e.g., bullet-only mode, abstractive vs extractive)
- **UI Changes**: React component state management is simple (useState only) - consider Context or Zustand for complexity
- **Additional Video Metadata**: Modify [backend/app/models/schemas.py](backend/app/models/schemas.py) and routes to return new fields

### Testing Considerations
- Mock YouTube Transcript API for unit tests (third-party dependency)
- Mock Gemini API responses for backend tests
- Mock axios calls in frontend tests

---

## Known Limitations & Tradeoffs

1. **Hardcoded Frontend API URL**: No env-driven configuration for API endpoint (change requires rebuild)
2. **Sync Gemini Call in Async Function**: Works because Flash is fast, but not ideal for slower models
3. **No Input Streaming**: Large transcripts sent as single prompt to Gemini
4. **Language Fallback Non-Deterministic**: `find_generated_transcript()` grabs first available auto-caption, which varies by video
5. **No Caching**: Every identical URL re-fetches and re-summarizes
6. **CORS Permissive**: `"*"` allows any origin in development

---

## When You Get Stuck

- **"Invalid YouTube URL"**: Check regex pattern in `extract_video_id()` - supports youtube.com, youtu.be, and /embed/
- **No transcript found**: Check `get_transcript()` fallback logic - some videos have no captions in any language
- **Gemini returns empty**: Check API quota and ensure prompt is correctly formatted
- **Frontend shows "Make sure backend is running!"**: Verify axios baseURL in api.js matches running server; check CORS headers
