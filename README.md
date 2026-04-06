# Retail-AI-Agent

Retail-AI-Agent is a lightweight full-stack prototype for a premium retail concierge experience. The project combines a Nuxt 3 frontend with a FastAPI backend, using a curated local product catalog to support conversational product discovery.

## Preview

![Retail-AI-Agent chat interface](docs/images/chat-home.png)

The current interface presents a centered glassmorphism chat surface with subtle motion, a soft mint-to-white background system, and a restrained visual language aligned with a high-end retail assistant.

## Highlights

- Nuxt 3 frontend with Tailwind CSS for layout and visual styling
- Naive UI installed for component expansion and future interface scaling
- FastAPI backend with file-based product retrieval from `backend/data/products.json`
- Lightweight product search endpoint without introducing database overhead
- Streaming `/chat` endpoint prepared for OpenAI-powered concierge responses
- Minimal conversational UI designed for premium retail discovery flows

## Architecture

```text
Retail-AI-Agent/
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |   `-- routes/
|   |   |       `-- health.py
|   |   |-- core/
|   |   |   `-- config.py
|   |   |-- __init__.py
|   |   `-- main.py
|   |-- data/
|   |   `-- products.json
|   |-- .env.example
|   `-- requirements.txt
|-- docs/
|   `-- images/
|       `-- chat-home.png
|-- frontend/
|   |-- assets/
|   |   `-- css/
|   |       `-- main.css
|   |-- components/
|   |-- pages/
|   |   `-- index.vue
|   |-- app.vue
|   |-- nuxt.config.ts
|   |-- package.json
|   |-- postcss.config.js
|   |-- tailwind.config.ts
|   `-- pnpm-lock.yaml
|-- .gitignore
`-- README.md
```

## Frontend Notes

The homepage is implemented as a minimal chat interface with:

- a centered frosted-glass container
- animated message entry with fade-in and slight upward motion
- a geometric assistant avatar and a soft circular user avatar
- a clean bottom input row focused on conversational interaction

The current frontend can be previewed independently even if the backend is not configured with an OpenAI API key yet.

## Backend Notes

The backend intentionally remains memory-conscious and operationally simple:

- product data is stored in `backend/data/products.json`
- product lookup is handled through direct file reads
- no relational or vector database is required for the current prototype stage
- the `/chat` route is structured for streamed text responses

This keeps the deployment footprint small while preserving a clear upgrade path for future retrieval or recommendation logic.

## Local Development

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

You can then open:

- [http://127.0.0.1:3000](http://127.0.0.1:3000)

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Environment Variables

Backend configuration is managed through `backend/.env`.

```env
APP_NAME=Retail-AI-Agent API
APP_VERSION=0.1.0
API_PREFIX=/api
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

## API Endpoints

- `GET /` basic service status
- `GET /api/health` health check
- `GET /api/products/search?keyword=...` lightweight file-based product search
- `POST /chat` streaming chat endpoint for conversational recommendations

## Current Scope

This repository is positioned as an interaction prototype rather than a production retail platform. It is best suited for:

- UI concept validation
- premium retail assistant demos
- early-stage conversational recommendation experiments
- lightweight end-to-end integration testing

## Next Steps

Recommended follow-up work for production hardening would include:

- structured recommendation tracing and analytics
- richer product attributes and multilingual prompt tuning
- authenticated environment management for the OpenAI integration
- more explicit response formatting between backend and frontend streaming layers