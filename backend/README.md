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

3) Run migrations (recommended even for SQLite):

```bash
cd backend
alembic upgrade head
```

4) Run the API (**current directory must be `backend/`** so `import app` works):

```bash

```

Windows PowerShell (one line from repo root `DATN`):

```powershell
Set-Location backend; python -m uvicorn app.main:app --reload --port 8000
```

If you ran uvicorn from `DATN/` (parent folder) you get `No module named 'app'` — always `cd backend` first.

Open docs at `http://localhost:8000/docs`.

Optional in `backend/.env` for AI features (Speaking, Writing, Translation, Vocab, Study plan):

```env
OPENROUTER_API_KEY=sk-or-v1-...
# Extra keys — rotated automatically when quota/rate-limit hit (recommended for 1000+ users)
# OPENROUTER_API_KEYS=sk-or-v1-key2,sk-or-v1-key3
OPENROUTER_FAST_MODEL=google/gemini-2.0-flash-001
# Production default: trycd backend
python -m uvicorn app.main:app --reload --port 8000 :free models first (no token cost, auto-failover across 6+ models)
# OPENROUTER_PREFER_FREE=true
```

The shared client (`app/core/openrouter_client.py`) cascades: **free models → paid primary → fallback**, rotates API keys on 402/429, and enables `provider.allow_fallbacks` on OpenRouter.

## Database migrations

Initial migration `20260524_initial_schema` uses **frozen DDL** (not `Base.metadata.create_all`) so fresh databases can run `alembic upgrade head` without duplicate table/column errors from later revisions.

```bash
cd backend
alembic upgrade head
```

## Next-week band prediction model

The dashboard "Dự báo" tab and Home banner call `GET /users/me/forecast/next-week`,
which loads a RandomForest model at `backend/model/next_week_ielts.joblib`
(path configurable via `NEXT_WEEK_MODEL_PATH`). The model is trained in the
standalone `ielts_model/` project and copied into the backend.

Build / refresh the artifact:

```bash
# from repo root
cd ielts_model
python src/generate_synthetic_ielts_data.py --students 600
python src/train_baseline_random_forest.py --n-estimators 60
# copy into the backend model dir
cp models/ielts_random_forest_baseline.joblib ../backend/model/next_week_ielts.joblib
```

Notes:
- Requires `scikit-learn` + `joblib` (already in `requirements.txt`).
- If the file is missing the endpoint degrades gracefully (`enabled=false`, cold start) — no crash.
- The model is **formative only**: it predicts next-week bands from weekly
  `score_history` aggregates and can warn the learner (in-app notification) when
  the predicted overall band does not improve. Với stack Docker gọn (`CELERY_ENABLED=false`),
  scan định kỳ không chạy — dự báo vẫn hoạt động khi user mở tab Dự báo.

## Admin user (one-time)

Admin is **not** auto-assigned by email at login/register. After a user registers, promote deliberately:

```bash
cd backend
python -m app.cli.promote_admin --email admin@example.com
```

Or SQL: `UPDATE users SET role='admin' WHERE email='admin@example.com';`

## Security notes (production)

| Topic | Configuration |
|-------|----------------|
| Secrets | `ENVIRONMENT=production` fails startup if `SECRET_KEY`, DB password, S3 keys, or `METRICS_TOKEN` look weak/default. Generate: `openssl rand -hex 32` |
| OpenAPI | `/docs`, `/redoc`, `/openapi.json` disabled when `ENVIRONMENT=production` |
| Metrics | `GET /metrics` requires `Authorization: Bearer <METRICS_TOKEN>` in production |
| Refresh token | Set `AUTH_HTTPONLY_REFRESH=true`; access token kept in memory on frontend (`tokenStore.js`) |
| History scores | `POST /history/save` is disabled (410) — use skill submit endpoints for server-side scoring |
| Rate limit | SlowAPI uses `X-Forwarded-For` only when the direct client is a trusted proxy; nginx also rate-limits auth/ML routes |

## Mock test JSON APIs (used by frontend)

- `GET /mock-tests`
- `GET /mock-tests?skill_id=1` (Reading) / `skill_id=2` (Listening)
- `GET /mock-tests/{id}`
- `GET /quizzes/{id}`

These endpoints read directly from `backend/data` and return the JSON with original field names.

#tạo bản đồ code cho AI 
gitnexus analyze