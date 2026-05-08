# Backend (FastAPI)

## Quick start (no Postgres required)

1) Create a virtual env (optional) and install deps:

```bash
cd backend
python -m pip install -r requirements.txt
```

2) Use SQLite (recommended for local demo):

- Edit `backend/.env` and set:

```env
DATABASE_URL=sqlite+aiosqlite:///./linguaielts.db
```

3) Run the API:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Open docs at `http://localhost:8000/docs`.

## Mock test JSON APIs (used by frontend)

- `GET /mock-tests`
- `GET /mock-tests?skill_id=1` (Reading) / `skill_id=2` (Listening)
- `GET /mock-tests/{id}`
- `GET /quizzes/{id}`

These endpoints read directly from `backend/data` and return the JSON with original field names.

