# Jarvis Control Tower

> **A Multi-Agent AI System with RAG, Workflow Automation, and Self-Monitoring**

Jarvis Control Tower is a personal AI orchestration platform that routes user messages through a multi-agent pipeline — classifying intent, planning actions, executing tasks, and quality-checking responses — all powered by **Ollama (llama3.2:3b)**, with vector memory (Qdrant), workflow automation (n8n), and a Telegram bot interface.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Services](#services)
  - [FastAPI — Core Orchestration](#fastapi--core-orchestration)
  - [Telegram Bot](#telegram-bot)
  - [Qdrant — Vector Memory](#qdrant--vector-memory)
  - [n8n — Workflow Automation](#n8n--workflow-automation)
- [Agent Pipeline](#agent-pipeline)
- [API Endpoints](#api-endpoints)
- [Dashboard](#dashboard)
- [n8n Workflows](#n8n-workflows)
- [Testing](#testing)
- [Security](#security)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Future Improvements](#future-improvements)

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        User Interfaces                          │
│     ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│     │  Telegram Bot │    │  Dashboard   │    │   REST API   │    │
│     │  @ind26bot    │    │  :8000/      │    │   :8000/api  │    │
│     └──────┬───────┘    └──────┬───────┘    └──────┬───────┘    │
│            │                   │                   │            │
│            └───────────────────┼───────────────────┘            │
│                                │                                │
│                    ┌───────────▼───────────┐                    │
│                    │    FastAPI Server     │                    │
│                    │  POST /orchestrate    │                    │
│                    └───────────┬───────────┘                    │
│                                │                                │
│             ┌──────────────────┼──────────────────┐             │
│             ▼                  ▼                  ▼             │
│     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│     │  Classifier  │→ │   Planner    │→ │   Executor   │→ ...  │
│     │  (Gemini)    │  │  (Gemini)    │  │  (Gemini)    │       │
│     └──────────────┘  └──────────────┘  └──────┬───────┘       │
│                                                │               │
│                     ┌──────────┬───────────────┤               │
│                     ▼          ▼               ▼               │
│              ┌──────────┐ ┌────────┐  ┌──────────────┐         │
│              │  Qdrant  │ │  n8n   │  │   Critic     │         │
│              │ (Memory) │ │(Flows) │  │  (Gemini)    │         │
│              └──────────┘ └────────┘  └──────────────┘         │
└──────────────────────────────────────────────────────────────────┘
```

**Flow:** User sends a message → Classifier identifies intent → Planner creates an action plan → Executor dispatches to services (LLM, Memory, n8n) → Critic quality-checks → Response returned.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **LLM** | Ollama (llama3.2:3b) | Local LLM inference — intent classification, planning, generation, quality checks |
| **Backend** | FastAPI (Python 3.11) | REST API, orchestration, agent pipeline |
| **Vector DB** | Qdrant | Semantic memory — conversations, knowledge, user preferences |
| **Workflows** | n8n | Automated workflows for reminders, health checks, notes |
| **Bot** | python-telegram-bot | Telegram interface using polling mode |
| **Frontend** | HTML/CSS/JS | Real-time monitoring dashboard |
| **Infra** | Docker Compose | Container orchestration for all services |

---

## Project Structure

```
jarvis-control-tower/
├── docker-compose.yml              # Container orchestration (4 services)
├── .env                            # Secrets (gitignored)
├── .env.example                    # Template for environment variables
├── .gitignore                      # Protects secrets from version control
├── Claude_Opus.md                  # This documentation file
│
├── services/
│   ├── fastapi/                    # Core AI orchestration service
│   │   ├── Dockerfile
│   │   ├── main.py                 # FastAPI app entrypoint + static file serving
│   │   ├── config.py               # Centralized settings (env vars)
│   │   ├── requirements.txt        # Python dependencies
│   │   ├── setup_n8n.py            # Script to deploy n8n workflows
│   │   ├── pytest.ini              # Test configuration
│   │   │
│   │   ├── agents/                 # Multi-agent pipeline
│   │   │   ├── base.py             # Abstract BaseAgent with timing/error handling
│   │   │   ├── classifier.py       # Intent classification agent
│   │   │   ├── planner.py          # Action planning agent
│   │   │   ├── executor.py         # Task execution agent (dispatches to services)
│   │   │   └── critic.py           # Response quality-checking agent
│   │   │
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic models (requests, responses, enums)
│   │   │
│   │   ├── routes/
│   │   │   ├── orchestrate.py      # POST /orchestrate — main AI pipeline
│   │   │   ├── health.py           # GET /health, /diagnostics, /runs, /trace
│   │   │   ├── memory.py           # POST /memory/store, /memory/search
│   │   │   └── n8n.py              # n8n workflow management (9 endpoints)
│   │   │
│   │   ├── services/
│   │   │   ├── ollama_client.py     # Ollama LLM API client
│   │   │   ├── qdrant_service.py   # Qdrant vector database client
│   │   │   ├── memory.py           # Memory service (search/store via Qdrant)
│   │   │   └── n8n_client.py       # n8n REST API client (CRUD + webhooks)
│   │   │
│   │   ├── logs/
│   │   │   └── runs.py             # In-memory execution run logger
│   │   │
│   │   ├── static/
│   │   │   ├── index.html          # Dashboard HTML
│   │   │   ├── styles.css          # Dark-themed CSS (glassmorphism design)
│   │   │   └── dashboard.js        # Live-polling dashboard logic
│   │   │
│   │   └── tests/
│   │       ├── conftest.py         # Shared fixtures (mocked Gemini, Qdrant, n8n)
│   │       ├── test_schemas.py     # 12 tests — Pydantic model validation
│   │       ├── test_config.py      # 4 tests — Settings defaults
│   │       ├── test_health.py      # 3 tests — Health/diagnostics routes
│   │       ├── test_n8n.py         # 8 tests — n8n management routes
│   │       └── test_agents.py      # 2 tests — BaseAgent framework
│   │
│   └── telegram-bot/               # Standalone Telegram bot service
│       ├── Dockerfile
│       ├── bot.py                  # Bot logic (/start, /help, /health + forwarding)
│       └── requirements.txt
│
└── app_data/                       # Persistent data volumes (Docker-managed)
```

---

## Services

### FastAPI — Core Orchestration

The central nervous system of Jarvis. It:

- **Orchestrates** the multi-agent pipeline (Classifier → Planner → Executor → Critic)
- **Manages** n8n workflows via REST API
- **Stores/retrieves** semantic memory via Qdrant
- **Serves** the monitoring dashboard
- **Logs** every execution run with full traces

**Port:** `8000`

### Telegram Bot

A standalone Python bot that connects to Telegram using **polling mode** (no HTTPS/webhooks needed for local development).

- Listens for messages on **@ind26bot**
- Forwards every text message to `POST /orchestrate`
- Returns Jarvis's response back to the user
- Supports commands: `/start`, `/help`, `/health`

**Why standalone?** The n8n Telegram Trigger node requires HTTPS webhook URLs, which don't work in local Docker. The standalone bot uses polling instead.

### Qdrant — Vector Memory

Qdrant provides **semantic search** over three collections:

| Collection | Purpose |
|-----------|---------|
| `conversations` | Chat history for context retrieval |
| `knowledge` | Stored facts and notes |
| `user_preferences` | User-specific settings and preferences |

Embeddings are generated using `BAAI/bge-small-en-v1.5` (384 dimensions).

**Port:** `6333`

### n8n — Workflow Automation

n8n provides visual workflow automation with webhook triggers. Five workflows are deployed:

| Workflow | Description |
|---------|-------------|
| Jarvis - Telegram Intake | Processes incoming Telegram messages |
| Jarvis - Reminder Scheduler | Schedules and manages reminders |
| Jarvis - Note Saver | Saves notes to the knowledge base |
| Jarvis - Health Check | Periodic system health monitoring |
| Jarvis - Intake (jarvi) | General-purpose intake webhook |

**Port:** `5678`

---

## Agent Pipeline

Every message passes through a **4-stage pipeline**, where each agent is powered by **Ollama (llama3.2:3b)**:

### 1. Classifier Agent

Analyzes the user's message and classifies it into one of six intents:

| Intent | Example |
|--------|---------|
| `reminder` | "Remind me to call mom at 5pm" |
| `note` | "Save this: the project deadline is Friday" |
| `question` | "What's the capital of France?" |
| `memory_update` | "Remember that I prefer dark mode" |
| `diagnostic` | "How are all systems doing?" |
| `unknown` | Anything that doesn't fit the above |

### 2. Planner Agent

Takes the classified intent and creates a **step-by-step action plan**. Example:

```json
{
  "steps": [
    { "action": "memory_search", "params": { "query": "user preferences" } },
    { "action": "llm_generate", "params": { "task": "answer" } }
  ]
}
```

### 3. Executor Agent

Dispatches each plan step to the appropriate service:

| Action | Service |
|--------|---------|
| `memory_search` | Qdrant (semantic search) |
| `memory_store` | Qdrant (store embedding) |
| `llm_generate` | Ollama (text generation) |
| `n8n_trigger` | n8n (webhook trigger) |
| `n8n_health_check` | n8n + Ollama (service health) |

### 4. Critic Agent

Quality-checks the executor's response before returning it to the user:
- Scores responses 1-10 on quality
- Can flag responses as needing improvement
- Ensures responses are helpful, accurate, and concise

---

## API Endpoints

### Core

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Dashboard UI |
| `POST` | `/orchestrate` | Main AI pipeline entry point |
| `GET` | `/health` | Basic health check |
| `GET` | `/diagnostics` | Full system diagnostics (all services) |
| `GET` | `/runs` | Recent execution runs |
| `GET` | `/trace/{run_id}` | Execution trace for a specific run |
| `GET` | `/trace/latest/run` | Most recent execution trace |

### Memory

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/memory/store` | Store text in vector memory |
| `POST` | `/memory/search` | Semantic search over memory |

### n8n Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/n8n/workflows` | List all workflows |
| `GET` | `/n8n/workflows/{id}` | Get a specific workflow |
| `POST` | `/n8n/workflows` | Create a new workflow |
| `DELETE` | `/n8n/workflows/{id}` | Delete a workflow |
| `POST` | `/n8n/workflows/{id}/activate` | Activate a workflow |
| `POST` | `/n8n/workflows/{id}/deactivate` | Deactivate a workflow |
| `GET` | `/n8n/executions` | List workflow executions |
| `POST` | `/n8n/webhook/{path}` | Proxy to n8n webhook |

---

## Dashboard

The Jarvis Control Tower dashboard is a **dark-themed, real-time monitoring UI** served at `http://localhost:8000/`.

### Features

- **Service Status Cards** — Live health indicators for Ollama, Qdrant, n8n, and Telegram Bot
- **n8n Workflow Table** — All deployed workflows with active/inactive status badges
- **Recent Runs** — Execution history with run IDs, intents, durations, and timestamps
- **Quick Test** — Built-in chatbox to send messages directly through the Jarvis pipeline
- **Auto-Refresh** — Polls all APIs every 15 seconds for real-time updates

### Design

- Dark navy/charcoal background with glassmorphism cards
- Cyan/teal accent colors with gradient highlights
- Smooth micro-animations and hover effects
- Responsive layout (works on desktop, tablet, and mobile)
- Inter font from Google Fonts

---

## Testing

**30 unit tests** covering all layers of the application:

```
tests/test_schemas.py     — 12 tests  (Pydantic models, enums, defaults)
tests/test_config.py      —  4 tests  (Settings, URLs, model config)
tests/test_health.py      —  3 tests  (Health check + diagnostics)
tests/test_n8n.py         —  8 tests  (All n8n management routes)
tests/test_agents.py      —  2 tests  (BaseAgent run + error handling)
tests/conftest.py         — Shared fixtures with mocked services
```

### Running Tests

```bash
docker exec jarvis-fastapi python -m pytest tests/ -v
```

All external services (Gemini, Qdrant, n8n) are mocked in tests using `unittest.mock`, so tests run **entirely offline** in under 2 seconds.

---

## Security

- **Secrets** are stored in `.env` (never committed to git)
- **`.gitignore`** excludes `.env`, `__pycache__`, and other sensitive files
- **`.env.example`** provides a safe template for sharing
- **API keys** are injected via Docker Compose environment variables
- The Gemini API key is scoped to the free tier (15 RPM / 1M tokens/day)

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- A [Google Gemini API key](https://aistudio.google.com/apikey) (free)
- A [Telegram Bot Token](https://core.telegram.org/bots#botfather) (optional, for Telegram integration)

### Setup

1. **Clone the repository:**

   ```bash
   git clone <repo-url>
   cd jarvis-control-tower
   ```

2. **Create your `.env` file** (copy from the template):

   ```bash
   cp .env.example .env
   ```

3. **Add your API keys** to `.env`:

   ```env
   GEMINI_API_KEY=your-gemini-api-key-here
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here
   ```

4. **Start all services:**

   ```bash
   docker compose up -d --build
   ```

5. **Deploy n8n workflows** (one-time setup):

   ```bash
   docker exec jarvis-fastapi python setup_n8n.py
   ```

6. **Open the dashboard:** [http://localhost:8000/](http://localhost:8000/)

### Verify Everything Works

- Dashboard shows **"All Systems Healthy"**
- All 4 service cards show **Online**
- The Quick Test input returns a response in **under 15 seconds**
- Run tests: `docker exec jarvis-fastapi python -m pytest tests/ -v`

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OLLAMA_URL` | ❌ | `http://ollama:11434` | Ollama service URL |
| `LLM_MODEL` | ❌ | `llama3.2:3b` | Ollama model to use |
| `LLM_TIMEOUT` | ❌ | `120` | Request timeout in seconds |
| `QDRANT_URL` | ❌ | `http://qdrant:6333` | Qdrant service URL |
| `N8N_URL` | ❌ | `http://n8n:5678` | n8n service URL |
| `N8N_API_KEY` | ✅ | — | n8n API authentication key |
| `N8N_BASIC_AUTH_USER` | ❌ | `admin` | n8n web UI username |
| `N8N_BASIC_AUTH_PASSWORD` | ❌ | `admin` | n8n web UI password |
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Telegram bot token from BotFather |
| `FASTAPI_URL` | ❌ | `http://jarvis-fastapi:8000` | FastAPI URL (for bot → API) |

---

## Running Containers

```
ollama                ✅  Port 11434 (LLM Inference)
jarvis-fastapi        ✅  Port 8000  (API + Dashboard)
jarvis-telegram-bot   ✅  Polling    (@ind26bot)
n8n                   ✅  Port 5678  (Workflow Engine)
qdrant                ✅  Port 6333  (Vector Database)
```

---

## Future Improvements

- [ ] **Streaming responses** — Stream Gemini output for real-time typing effect
- [ ] **Conversation history** — Store and retrieve multi-turn conversations
- [ ] **Agent memory** — Agents remember context across sessions via Qdrant
- [ ] **Authentication** — API key or JWT auth for the FastAPI endpoints
- [ ] **CI/CD** — GitHub Actions for automated testing and deployment
- [ ] **Prometheus + Grafana** — Production-grade monitoring and alerting
- [ ] **Multi-model support** — Hot-swap between Gemini, GPT-4, Claude, etc.
- [ ] **Voice interface** — Whisper STT + TTS for voice-based interaction
- [ ] **Plugin system** — Dynamically load new agents and capabilities
- [ ] **Rate limiting** — Protect API endpoints from excessive usage

---

*Built with ⚡ by the Jarvis Control Tower team*
