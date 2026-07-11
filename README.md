# VibeAI

**VibeAI** is an AI-powered, mood-based entertainment assistant. Tell it how you feel (in Persian) and it analyzes your mood, energy level, current activity, and time of day, then recommends movies and music tailored to your emotional state — each with a human-readable explanation of *why* it was picked.

Built as a chat-style experience: every conversation is a session, and every message in it produces a fresh mood analysis plus recommendations.

## Features

- **Hybrid mood analysis** — a rule-based Persian NLP engine (keyword/negation detection) with an optional Gemini-powered layer for deeper sentiment understanding, and automatic fallback if the LLM is unavailable.
- **Explainable recommendations** — movies (via TMDB) and music (via a curated dataset + Spotify metadata) are ranked with a visible reasoning trail, not a black box.
- **Content-intent detection** — asking specifically for "a movie" or "a song" narrows and focuses the results.
- **Personalization loop** — like/dislike feedback builds a taste profile (favorite genres) that influences future ranking.
- **Chat history & mood journal** — every chat is persisted; mood trends over time are surfaced in the UI.
- **Safety layer** — sensitive/crisis-adjacent moods trigger a content safety mode instead of default recommendations.
- **Resilient by design** — TMDB/Spotify/Gemini outages degrade gracefully (mock data / rule-based fallback) instead of crashing the API.
- **Rate limiting** — 30 requests/minute per client via `slowapi`.

## Tech Stack

| Layer      | Technology |
|------------|------------|
| Backend    | Python, FastAPI, Pydantic, SQLAlchemy, SQLite, slowapi |
| Mood AI    | Rule-based Persian analyzer + Google Gemini (`google-genai`) |
| Data       | TMDB API, Spotify Web API, local music dataset |
| Frontend   | React 19, Vite, Tailwind CSS, Framer Motion |
| Testing    | pytest, pytest-asyncio, httpx |

## Architecture

```
frontend-react/        React SPA (chat UI, mood journal, trends, reminders)
Backend/
├── app.py             FastAPI app & route definitions
├── api/                Feedback / history / recommend route helpers
├── mood/               Hybrid mood analyzer (rule-based + Gemini + fallback)
├── recommender/         Movie & music ranking, reasoning, safety, personalization
├── services/           TMDB / Spotify / YouTube integrations
├── database/            SQLAlchemy models, schema, persistence layer
├── cache/               Lightweight response caching
├── config/              Settings & constants
└── tests/               pytest suite
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- API keys (all optional — the app degrades gracefully without them):
  - [TMDB](https://www.themoviedb.org/settings/api) — movie recommendations
  - [Spotify](https://developer.spotify.com/dashboard) — music metadata (Client Credentials flow)
  - [Gemini](https://aistudio.google.com/) — smarter mood analysis (falls back to rule-based otherwise)

### Backend setup

```bash
cd Backend
python -m venv venv
venv\Scripts\activate        # on Windows
# source venv/bin/activate   # on macOS/Linux

pip install -r requirements.txt
copy .env.example .env       # on Windows; use `cp` on macOS/Linux
# then fill in your API keys in .env

python app.py
```

The API will be available at `http://127.0.0.1:8000`, with interactive docs at `http://127.0.0.1:8000/docs`.

### Frontend setup

```bash
cd frontend-react
npm install
npm run dev
```

The app will be available at `http://localhost:5173` and talks to the backend at `http://127.0.0.1:8000` by default (see `src/lib/api.js`).

### Running tests

```bash
cd Backend
pytest
```

## API Overview

| Method | Endpoint              | Description                                   |
|--------|-----------------------|------------------------------------------------|
| POST   | `/api/analyze`        | Analyze Persian text for mood/energy/activity  |
| POST   | `/api/chats`          | Create a new chat session                      |
| GET    | `/api/chats`          | List chats (with search)                       |
| GET    | `/api/chats/{id}`     | Get a chat with its full message history       |
| POST   | `/api/recommend`      | Analyze + recommend movies/music in one call   |
| POST   | `/api/feedback`       | Submit like/dislike feedback on a recommendation |
| GET    | `/api/history`        | Global recommendation history                  |
| GET    | `/api/taste-profile`  | Learned genre preferences from feedback        |

Full request/response schemas are available via the auto-generated OpenAPI docs at `/docs` once the backend is running.

## License

Released under the [MIT License](LICENSE).
