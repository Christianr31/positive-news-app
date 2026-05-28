# Positive News Globe (MVP)

A green-themed web app that shows weekly positive stories around the world on an interactive globe.

## Stack

- Frontend: React + Vite + globe.gl
- Backend: FastAPI (Python) + NewsAPI integration

## News API Setup (Real Data)

1. Create a free API key at [NewsAPI](https://newsapi.org/).
2. In `backend`, copy `.env.example` to `.env`.
3. Set `NEWS_API_KEY` in `.env`.

If `NEWS_API_KEY` is missing, the app automatically uses built-in demo fallback stories.

## Run Backend

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Backend runs on `http://127.0.0.1:8000`.

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://127.0.0.1:5173`.

## Features in this MVP

- Center title bar: **Positive News**
- 3D rotating globe with clickable location markers
- Weekly biggest positive stories panel
- Location-specific story cards on click
- Green visual theme designed for smooth, modern look
- Pulls real weekly positive stories when API key is configured
