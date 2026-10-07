# VerifyAI

VerifyAI is an end-to-end AI content verification platform that detects misinformation, deepfakes, synthetic media, and manipulated content across text, image, audio, and video inputs.

## Overview

In a world of generative AI, trust is the next critical infrastructure. VerifyAI gives teams and individuals a fast way to:

- analyze content for signs of AI generation
- score source credibility and risk
- review evidence and explainability trails
- manage verification workflows
- monitor dashboard activity over time

## Solution Architecture

- Frontend: React + TypeScript dashboard
- Backend: FastAPI service with SQLite persistence
- AI Detection Service: Python-based verification service for rule-based and LLM-assisted analysis
- Containerized deployment: Docker Compose

## Key Features

- content verification requests
- trust and risk scoring
- source credibility checks
- dashboard analytics
- auth and user flows
- direct AI detection endpoints

## Quick Start

### Prerequisites

- Docker + Docker Compose
- Node.js 20+
- Python 3.11+

### Run with Docker

```bash
docker compose up --build
```

This starts:

- frontend on http://localhost:5173
- backend on http://localhost:8000
- ai-service on http://localhost:8001
- PostgreSQL on localhost:5432 (if included in the compose file)

### Manual local setup

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

AI service:

```bash
cd ai-service
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Frontend:

```bash
cd web
npm install
npm run dev
```

## Default Demo Credentials

- Email: demo@verifyai.app
- Password: verifyai123

## API Examples

### Health check

```bash
curl http://localhost:8000/api/health
```

### Submit content for verification

```bash
curl -X POST http://localhost:8000/api/verifications \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Campaign clip",
    "content_type": "image",
    "content_text": "A dramatic image of a public figure in a manipulated setting.",
    "source_url": "https://example.com/post",
    "source_name": "Example Media"
  }'
```

## Tech Notes

This MVP focuses on a working end-to-end product architecture with explainability and operational flow. It includes realistic verification scoring and dashboard logic, designed to be extended with real ML models and production-grade services.

## License

MIT
