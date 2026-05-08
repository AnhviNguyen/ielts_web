# Frontend (Vue + Vite)

## Run

```bash
cd fronted
npm install
npm run dev
```

Open `http://localhost:5173`.

## API connectivity

Frontend calls API via `/api/*` (Axios baseURL = `/api`).
Vite proxies `/api` to `http://localhost:8000` and strips the `/api` prefix.

So the backend must expose:

- `/mock-tests`
- `/mock-tests/{id}`
- `/quizzes/{id}`

## Audio CDN (Listening)

Set `fronted/.env`:

```env
VITE_AUDIO_CDN_BASE=
VITE_AUDIO_CDN_EXT=.mp3
```

Audio URL is built from `part.file_id` as:
`{VITE_AUDIO_CDN_BASE}/{file_id}{VITE_AUDIO_CDN_EXT}`.

