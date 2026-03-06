# Moment Trigger Assistant

Moment Trigger Assistant is an AI-powered platform that combines real-time weather and location intelligence to propose moment-based retail marketing activations near relevant points of interest (POIs).

It is designed as a three-service system:
- An MCP server that gathers geospatial and weather context
- An LLM agent that orchestrates tool calls and produces activation plans
- A React dashboard chat interface for marketers and operators

## 1) Architecture Overview

```text
┌──────────────────────────────────────────────────────────────┐
│                      Frontend (React)                       │
│      Chat UI (Tailwind) + markdown rendering + badges       │
└──────────────────────────────┬───────────────────────────────┘
															 │ POST /chat
															 ▼
┌──────────────────────────────────────────────────────────────┐
│                   Agent API (FastAPI)                       │
│      LangChain + Groq llama-3.3-70b-versatile              │
│      Tools: weather, geocode, POIs, geofence               │
└──────────────────────────────┬───────────────────────────────┘
															 │ HTTP tool calls
															 ▼
┌──────────────────────────────────────────────────────────────┐
│                    MCP Server (FastAPI)                     │
│      Routes/Services/Models for location intelligence        │
└───────────────┬───────────────────┬───────────────────┬──────┘
								│                   │                   │
								▼                   ▼                   ▼
				Open-Meteo API       Nominatim API       Overpass API
																									(OSM POIs)
```

## 2) Tech Stack

### MCP Server
- FastAPI
- httpx
- Pydantic

### Agent
- LangChain
- Pinned package versions:
	- `langchain==0.3.25`
	- `langchain-core==0.3.59`
	- `langchain-groq==0.3.2`
- Groq model: `llama-3.3-70b-versatile`
- FastAPI
- httpx

### Frontend
- React 18
- Axios
- Tailwind CSS
- react-markdown

### External APIs
- Open-Meteo
- Nominatim
- Overpass API
- Groq

Note: Overpass free API is used in this project for demo purposes. For production workloads, prefer a managed POI provider such as Foursquare Places API or Google Places API.

## 3) Prerequisites

- Python `3.10+`
- Node.js `18+`
- npm (bundled with Node)
- Groq API key

## 4) Local Setup (All 3 Services)

Run services in this order:
1. `mcp-server`
2. `agent`
3. `frontend`

### A. MCP Server Setup

```bash
cd mcp-server
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

### B. Agent Setup

```bash
cd agent
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python main.py
```

Health check:

```bash
curl http://localhost:8001/health
```

### C. Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
npm start
```

Default UI URL:

```text
http://localhost:3000
```

## Docker Compose Quick Start

1. Copy root `.env.example` to `.env` and fill in keys:

	```bash
	cp .env.example .env
	```

2. Build and start all 3 services:

	```bash
	docker compose up --build
	```

3. Open http://localhost:3000

Services:
- `mcp-server`: http://localhost:8000
- `agent`: http://localhost:8001
- `frontend`: http://localhost:3000

Note: Docker must be installed on your machine.

## 5) Environment Variables

### `mcp-server/.env`

From `.env.example`:

```dotenv
HOST=0.0.0.0
PORT=8000
```

Notes:
- Current runtime command in this repo explicitly passes host/port via `uvicorn` CLI.
- If you add server bootstrap configuration later, these values can be read directly in code.

### `agent/.env`

```dotenv
GROQ_API_KEY=your_groq_api_key
MCP_SERVER_URL=http://localhost:8000
```

Required:
- `GROQ_API_KEY`: authenticates requests to Groq.
- `MCP_SERVER_URL`: base URL of the MCP server the agent tools call.

### `frontend/.env`

```dotenv
REACT_APP_API_URL=http://localhost:8001
```

Notes:
- The current chat UI posts to `http://localhost:8001/chat`.
- You can standardize this via `REACT_APP_API_URL` if you want environment-specific frontend routing.

## 6) Example Queries

Use these in the chat UI or via API:

- `Check New York weather and suggest a marketing campaign for nearby grocery stores`
- `Find coffee shops near Jersey City NJ and suggest a cold weather activation`
- `Find gyms near Austin TX and suggest a morning workout activation`
- `Find Target near Seattle and recommend a geofence strategy`

Direct API example:

```bash
curl -X POST http://localhost:8001/chat \
	-H "Content-Type: application/json" \
	-d '{"message":"Find coffee shops near Jersey City NJ and suggest a cold weather activation"}'
```

Expected response shape:

```json
{
	"response": "...markdown plan...",
	"tools_used": ["get_weather", "geocode_location", "search_pois", "suggest_geofence"]
}
```

## 7) Deployment (Docker Approach)

Recommended pattern: one container per service, orchestrated with Docker Compose.

### Suggested Containerization Strategy

- `mcp-server` container
	- Base image: `python:3.11-slim`
	- Installs `mcp-server/requirements.txt`
	- Runs: `uvicorn main:app --host 0.0.0.0 --port 8000`

- `agent` container
	- Base image: `python:3.11-slim`
	- Installs `agent/requirements.txt`
	- Environment includes `GROQ_API_KEY` and `MCP_SERVER_URL=http://mcp-server:8000`
	- Runs: `python main.py` (or `uvicorn main:app --host 0.0.0.0 --port 8001`)

- `frontend` container
	- Multi-stage build (`node:18` build stage + lightweight web server runtime)
	- Build-time/public env for API base URL
	- Exposes port `3000` (or static serve port)

### Compose-Level Best Practices

- Use an internal network so `agent` can call `mcp-server` by service name.
- Add healthchecks for all services (`/health` endpoints for Python services).
- Use restart policies for resilience (`unless-stopped` in dev/prod-lab environments).
- Externalize secrets (Groq key) via environment/secret management, not in source control.

## 8) Documentation Philosophy (For New Developers)

This project follows a practical, operations-friendly documentation style:

- **Architecture-first**: explain service boundaries and runtime flow before implementation details.
- **Contract-driven**: document request/response schemas and error behaviors for each service boundary.
- **Reproducible setup**: onboarding steps must be copy/paste runnable with explicit versions.
- **Observability-aware**: health checks, timeout behavior, and upstream dependencies are documented alongside features.
- **Incremental depth**: keep root docs concise but link to deeper docs as complexity grows (e.g., API docs, runbooks, troubleshooting guides).

When adding new features, update docs in the same PR for:
1. API contract changes
2. New environment variables
3. Local run/deploy impact
4. Example query or usage updates

## Repository Structure

```text
.
├── agent/
│   ├── agent.py
│   ├── config.py
│   ├── main.py
│   ├── requirements.txt
│   └── tools.py
├── frontend/
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── index.css
│       └── index.jsx
├── mcp-server/
│   ├── config.py
│   ├── main.py
│   ├── models/
│   ├── requirements.txt
│   ├── routes/
│   └── services/
└── README.md
```
