<p align="center">
  <span style="font-size: 3rem">⚡</span>
</p>

<h1 align="center">Jarvis Control Tower</h1>

<p align="center">
  <strong>Multi-Agent AI System with RAG, Self-Monitoring, and Workflow Automation</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white" alt="Ollama" />
  <img src="https://img.shields.io/badge/n8n-EA4B71?style=for-the-badge&logo=n8n&logoColor=white" alt="n8n" />
  <img src="https://img.shields.io/badge/Qdrant-DC382D?style=for-the-badge&logo=qdrant&logoColor=white" alt="Qdrant" />
</p>

---

## Overview

Jarvis Control Tower is a production-ready, self-hosted AI orchestration system that routes user messages through a **6-agent pipeline**, persists everything to **PostgreSQL**, uses **Qdrant** for semantic memory (RAG), automates workflows via **n8n**, and exposes a real-time **dashboard** for monitoring.

It's designed to work as a personal AI assistant accessible via **Telegram**, with pluggable LLM backends (Ollama, OpenAI, Gemini, etc.).

---

## Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────┐
│  Telegram   │────▶│           FastAPI Orchestrator            │
│    Bot      │◀────│                                          │
└─────────────┘     │  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
                    │  │Classifier│─▶│ Planner │─▶│Researcher│  │
┌─────────────┐     │  └─────────┘  └─────────┘  └────┬────┘  │
│  Dashboard  │────▶│                                   │      │
│  (Web UI)   │     │  ┌─────────┐  ┌──────────┐  ┌───▼────┐  │
└─────────────┘     │  │  Critic │◀─│Tool Router│◀─│Executor│  │
                    │  └─────────┘  └──────────┘  └────────┘  │
                    └──────────┬───────────┬───────────────────┘
                               │           │
                    ┌──────────▼──┐  ┌─────▼─────┐  ┌─────────┐
                    │  PostgreSQL  │  │   Qdrant   │  │   n8n   │
                    │  (6 tables)  │  │ (3 colls)  │  │(7 flows)│
                    └─────────────┘  └───────────┘  └─────────┘
```

### Agent Pipeline

| # | Agent | Role |
|---|-------|------|
| 1 | **Classifier** | Detects intent (question, reminder, note, greeting, etc.) |
| 2 | **Planner** | Generates a step-by-step action plan |
| 3 | **Researcher** | Searches Qdrant for relevant context (conversations, knowledge, preferences) |
| 4 | **Executor** | Executes the plan using LLM + context |
| 5 | **Tool Router** | Routes to tools: creates reminders, stores notes in Postgres + Qdrant |
| 6 | **Critic** | Quality-checks the response, can trigger re-execution |

---

## Tech Stack

| Service | Technology | Purpose |
|---------|-----------|---------|
| **API Server** | FastAPI (Python 3.11) | Orchestration, routing, REST API |
| **LLM** | Ollama (llama3.2:3b) | Intent classification, planning, response generation |
| **Vector DB** | Qdrant | Semantic search, RAG, memory embeddings |
| **Database** | PostgreSQL 16 | Runs, steps, users, notes, reminders, error logs |
| **Workflows** | n8n | Reminder scheduler, health checks, error catching |
| **Bot** | python-telegram-bot | Telegram interface |
| **Embeddings** | FastEmbed (BAAI/bge-small-en-v1.5) | Text → vector embeddings |

---

## Features

- 🤖 **6-Agent Pipeline** — Classify → Plan → Research → Execute → Route Tools → Critique
- 🧠 **RAG Memory** — Semantic search across conversations, knowledge, and user preferences via Qdrant
- 🐘 **Full Persistence** — Every run, agent step, note, and reminder stored in PostgreSQL
- ⏰ **Smart Reminders** — Natural language time parsing, stored in Postgres, delivered via n8n cron + Telegram
- 📊 **Real-time Dashboard** — Dark-themed UI with service health, workflow status, run drill-down with agent timeline
- 🔧 **Tool Endpoints** — Memory write, reminder create, RAG ingest, error diagnosis
- 🔄 **7 n8n Workflows** — Reminder scheduler, health check, Telegram intake, note saver, ingest handler, error catcher
- ✅ **30 Unit Tests** — Agents, routes, config, schemas all tested

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))

### 1. Clone and Configure

```bash
git clone https://github.com/yourusername/jarvis-control-tower.git
cd jarvis-control-tower

# Copy example env and fill in your values
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token

# n8n
N8N_API_KEY=your-n8n-api-key

# Postgres
POSTGRES_USER=jarvis
POSTGRES_PASSWORD=jarvis_secret
POSTGRES_DB=jarvis_db
DATABASE_URL=postgresql://jarvis:jarvis_secret@postgres:5432/jarvis_db
```

### 2. Start All Services

```bash
docker compose up -d --build
```

This starts 6 containers:
- `ollama` — LLM inference (port 11434)
- `qdrant` — Vector database (port 6333)
- `jarvis-postgres` — PostgreSQL (port 5432)
- `n8n` — Workflow automation (port 5678)
- `jarvis-fastapi` — API server (port 8000)
- `jarvis-telegram-bot` — Telegram bot

### 3. Pull the LLM Model

```bash
docker exec ollama ollama pull llama3.2:3b
```

### 4. Deploy n8n Workflows

```bash
docker exec jarvis-fastapi python setup_n8n.py
```

### 5. Open the Dashboard

Navigate to [http://localhost:8000](http://localhost:8000) to see the control tower dashboard.

---

## API Endpoints

### Core

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/orchestrate` | Main pipeline — full 6-agent orchestration |
| `GET` | `/health` | Simple health check |
| `GET` | `/diagnostics` | Detailed service health (Ollama, Qdrant, n8n, Postgres) |

### Tools

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/tools/memory_write` | Store a note in Postgres (+ optional Qdrant embed) |
| `POST` | `/tools/reminder_create` | Schedule a reminder |
| `GET` | `/tools/reminders/due` | Get all due reminders (used by n8n cron) |
| `POST` | `/tools/reminders/{id}/sent` | Mark a reminder as sent |

### RAG & Diagnosis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/rag/ingest` | Chunk and embed text into Qdrant |
| `POST` | `/diagnose` | Submit an error for LLM-powered diagnosis |
| `GET` | `/diagnose/errors` | List recent workflow errors |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/dashboard/runs` | Recent orchestration runs |
| `GET` | `/dashboard/runs/{run_id}` | Detailed run with agent steps |

### Memory & n8n

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/memory/store` | Store text in Qdrant |
| `POST` | `/memory/search` | Semantic search in Qdrant |
| `GET` | `/n8n/workflows` | List all n8n workflows |

---

## Project Structure

```
jarvis-control-tower/
├── docker-compose.yml              # 6-service orchestration
├── .env.example                    # Environment template
│
├── services/
│   ├── fastapi/                    # Main API server
│   │   ├── main.py                 # FastAPI app + lifespan
│   │   ├── config.py               # Settings + env vars
│   │   ├── setup_n8n.py            # n8n workflow deployer
│   │   │
│   │   ├── agents/                 # 6-agent pipeline
│   │   │   ├── base.py             # BaseAgent (timing, error handling)
│   │   │   ├── classifier.py       # Intent classification
│   │   │   ├── planner.py          # Action planning
│   │   │   ├── researcher.py       # Qdrant RAG search
│   │   │   ├── executor.py         # LLM execution
│   │   │   ├── tool_router.py      # Tool dispatch (reminders, notes)
│   │   │   └── critic.py           # Quality validation
│   │   │
│   │   ├── routes/                 # API endpoints
│   │   │   ├── orchestrate.py      # POST /orchestrate
│   │   │   ├── health.py           # Health + dashboard endpoints
│   │   │   ├── tools.py            # Memory write, reminders
│   │   │   ├── ingest.py           # RAG ingestion
│   │   │   ├── diagnose.py         # Error diagnosis
│   │   │   ├── memory.py           # Qdrant memory ops
│   │   │   └── n8n.py              # n8n workflow management
│   │   │
│   │   ├── services/               # Backend services
│   │   │   ├── database.py         # Async PostgreSQL client
│   │   │   ├── ollama_client.py    # LLM client
│   │   │   ├── qdrant_service.py   # Vector DB client
│   │   │   └── memory.py           # Memory service (Qdrant)
│   │   │
│   │   ├── static/                 # Dashboard UI
│   │   │   ├── index.html
│   │   │   ├── styles.css
│   │   │   └── dashboard.js
│   │   │
│   │   └── tests/                  # 30 unit tests
│   │       ├── test_agents.py
│   │       ├── test_config.py
│   │       ├── test_health.py
│   │       ├── test_n8n.py
│   │       └── test_schemas.py
│   │
│   ├── postgres/
│   │   └── init.sql                # Schema: 6 tables + indexes
│   │
│   └── telegram-bot/
│       ├── bot.py                  # Telegram polling bot
│       └── Dockerfile
```

---

## Database Schema

PostgreSQL stores 6 tables:

| Table | Purpose |
|-------|---------|
| `users` | User profiles (auto-created on first message) |
| `runs` | Orchestration runs (input, intent, status, reply, duration) |
| `run_steps` | Per-agent steps (input/output JSON, latency, errors) |
| `notes` | User notes/facts with tags and optional Qdrant links |
| `reminders` | Scheduled reminders (pending → sent) |
| `workflow_errors` | n8n error logs with LLM-generated diagnoses |

---

## n8n Workflows

7 workflows are auto-deployed via `setup_n8n.py`:

| Workflow | Type | Description |
|----------|------|-------------|
| **Reminder Scheduler** | Cron (1 min) | Polls due reminders → sends via Telegram → marks sent |
| **Health Check** | Cron (30 min) | Pings `/diagnostics` |
| **Telegram Intake** | Webhook | Routes Telegram messages to `/orchestrate` |
| **Note Saver** | Webhook | Stores notes via `/tools/memory_write` |
| **Ingest Handler** | Webhook | Feeds text into `/rag/ingest` |
| **Error Catcher** | Webhook | Sends errors to `/diagnose` → alerts via Telegram |
| **Jarvis Bot** | Webhook | Core Telegram bot workflow |

---

## Running Tests

```bash
# Install test dependencies and run
docker exec jarvis-fastapi pip install pytest pytest-asyncio respx -q
docker exec jarvis-fastapi python -m pytest tests/ -v
```

Expected: **30/30 tests passing**.

---

## Dashboard

The dashboard at [http://localhost:8000](http://localhost:8000) provides:

- **Service Health** — Real-time status of Ollama, Qdrant, n8n, Postgres, Telegram
- **Workflow Monitor** — All 7 n8n workflows with active/inactive status
- **Run History** — Clickable table of recent orchestration runs
- **Run Detail Modal** — Agent timeline with latency bars, JSON output, error highlighting
- **Quick Test** — Send messages directly from the browser

Auto-refreshes every 15 seconds.

---

## Configuration

All configuration is via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://ollama:11434` | LLM service URL |
| `QDRANT_URL` | `http://qdrant:6333` | Vector DB URL |
| `N8N_URL` | `http://n8n:5678` | Workflow engine URL |
| `DATABASE_URL` | — | PostgreSQL connection string |
| `TELEGRAM_BOT_TOKEN` | — | Telegram bot token |
| `N8N_API_KEY` | — | n8n API key for workflow management |
| `POSTGRES_USER` | `jarvis` | Database user |
| `POSTGRES_PASSWORD` | — | Database password |
| `POSTGRES_DB` | `jarvis_db` | Database name |

---

## Performance Note

The default setup uses **Ollama with llama3.2:3b running on CPU** inside Docker, which can be slow for the full 6-agent pipeline. For faster responses:

1. **Cloud LLM** — Swap Ollama for OpenAI/Gemini API calls
2. **Native Ollama** — Run Ollama on your host machine with GPU acceleration and point `OLLAMA_URL` to `http://host.docker.internal:11434`
3. **Smaller Model** — Use `tinyllama` or `phi3:mini` for faster CPU inference

The tool endpoints (`/tools/reminder_create`, `/tools/memory_write`, `/rag/ingest`) work **instantly** without the LLM.

---

## License

MIT

---

<p align="center">
  Built with ⚡ by <a href="https://github.com/yourusername">Indu</a>
</p>
