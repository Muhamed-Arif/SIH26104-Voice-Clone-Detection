# AetherVoice Frontend

This folder contains the React/Vite/Three.js frontend supplied by the frontend team and integrated with the SIH26104 backend.

## Live integration

The **Live Analysis** page uses the existing backend contract directly:

- microphone capture: native browser sample rate, mono
- live window: 2 seconds
- hop: 1 second
- silence gate: -45 dBFS
- API: `POST /api/v1/analyze`
- backend response fields used: `synthetic_probability`, `confidence`, `risk_score`, `risk_level`, `action`, `model_version`, `reason_codes`
- health: `GET /integration-health`

No hard-coded JWT or session token is stored in the frontend. Each browser session generates its own UUID.

## Development

```powershell
cd frontend
npm ci
npm run dev
```

By default the frontend uses the same origin as the backend. For a separate Vite development server, set:

```powershell
$env:VITE_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

## Production build used by the integrated backend

From the repository root:

```powershell
.\build_frontend.ps1
```

This builds the React application and copies `frontend/dist/*` into `backend/app/static/aethervoice/`. The FastAPI server then serves AetherVoice at `http://127.0.0.1:8000/`.
