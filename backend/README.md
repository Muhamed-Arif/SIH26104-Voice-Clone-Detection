# SIH26104: AI-Powered Real-Time Detection and Prevention of Voice Cloning Impersonation Attacks

Backend Integration & Service Layer (Member 3 - Backend Engineer).

---

## Architecture Overview

This backend acts as the central orchestrator and integration hub for the anti-voice spoofing system. It bridges real-time DSP audio streaming (Member 2), ML model inference (Member 1), risk calculation, prevention triggers (Member 5), persistent database auditing, and frontend interaction (Member 4).

```
backend/
├── main.py                     # FastAPI entry point, CORS, lifespan, global error handlers
├── alembic.ini                 # Alembic migration configuration
├── alembic/                    # Async DB migration scripts
│   ├── env.py
│   └── versions/0001_initial_schema.py
├── app/
│   ├── api/v1/                 # REST & WebSocket API endpoints (sessions, analyze, stream, results, verify)
│   ├── core/                   # Base settings, structured JSON logger, domain exceptions
│   ├── database/               # SQLAlchemy 2.0 async engine, 6 models, 4 repository abstractions
│   ├── risk_engine/            # Risk calculator, named thresholds, human-readable reason codes
│   ├── schemas/                # Pydantic v2 schemas matching external contracts & uniform errors
│   ├── security/               # JWT authentication, role authorization, rate limiter, input validation
│   ├── services/               # Audio orchestrator, ML client (swappable), session manager, prevention
│   └── websocket/              # Native WebSocket connection manager & stream frame handler
├── tests/                      # Pytest suite with in-memory SQLite fixtures (18 automated tests)
├── Dockerfile                  # Containerized deployment
├── requirements.txt            # Python dependencies
├── .env.example                # Documented environment variables
└── README.md
```

---

## Quickstart & Local Setup

### 1. Environment & Dependencies
```bash
# Create and activate Python virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS

# Install requirements
pip install -r backend/requirements.txt
```

### 2. Configuration
Copy `.env.example` to `.env`:
```bash
cp backend/.env.example backend/.env
```

### 3. Database Migrations (MySQL)
Run Alembic migrations:
```bash
cd backend
alembic upgrade head
```

### 4. Running the Development Server
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- Interactive API Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- OpenAPI Schema JSON: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### 5. Running Automated Tests
```bash
python -m pytest backend/tests -v
```

---

## Team Interface Contracts

Complete schema definitions and payload contracts for Members 1, 2, 4, 5, and 6 are documented in [docs/contracts.md](file:///c:/Users/GOPISH/OneDrive/Desktop/SIH/docs/contracts.md).
