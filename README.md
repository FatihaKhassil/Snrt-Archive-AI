# 🎙️ SNRT Smart Archive AI

[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Deploy-Docker%20Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/License-TBD-lightgrey)](#license)

This is a project I built to turn SNRT's scattered documents and audio recordings
into something you can actually search and talk to. Drop in a file, and my
platform extracts the text, transcribes the audio, indexes everything, and lets
you find what you need through keyword search, semantic search, or plain-language
questions (RAG-powered).

## What it does

- Upload documents and audio files
- Extract text from documents (Apache Tika)
- Transcribe audio (Whisper)
- Enrich content automatically with an LLM
- Keyword search (Apache Solr)
- Semantic search via embeddings (ChromaDB)
- Ask questions in natural language and get answers grounded in the archives (RAG)
- User accounts, roles, and basic monitoring (Prometheus, Grafana)

## How a file moves through my system

```text
Upload
  │
  ▼
FastAPI ──► MongoDB + file storage ──► Kafka
                                          │
                ┌─────────────────────────┴─────────────────────────┐
                ▼                                                   ▼
        Document → Apache Tika                              Audio → Whisper
                └─────────────────────────┬─────────────────────────┘
                                          ▼
                                  Extracted / transcribed text
                                          │
                                          ▼
                                   LLM enrichment
                                    ┌─────┴─────┐
                                    ▼           ▼
                              Apache Solr   ChromaDB
                              (keyword)   (semantic / RAG)
```

Everything after the upload runs asynchronously through Kafka, so my API stays
responsive while the heavy lifting (transcription, enrichment, indexing) happens
in the background.

## Project layout

| Folder | What's in it |
|---|---|
| `frontend` | React + Vite + Material UI web app |
| `backend-fastapi` | REST API — upload, search, RAG, auth, users, stats |
| `workers/audio-worker` | Audio transcription (Whisper) |
| `workers/document-worker` | Document text extraction (Tika) |
| `workers/llm-worker` | Content enrichment |
| `workers/embedding-worker` | Chunking + embeddings → ChromaDB |
| `workers/solr-worker` | Indexing into Solr |
| `prometheus` / `grafana` / `loki` | Metrics, dashboards, logs |
| `storage` | Shared local volume for uploaded files |

## Tech stack

React · Vite · Material UI · FastAPI · Apache Kafka · MongoDB · Apache Tika ·
OpenAI Whisper · Apache Solr · ChromaDB · Ollama (`nomic-embed-text`) · Groq / Ollama LLM ·
Prometheus · Grafana · Loki · Docker Compose

## Getting started

**Requirements:** Docker, Docker Compose, and a `.env` file at the project root
(I've kept my own credentials out of version control, of course).

```bash
docker compose up --build -d
```

Then pull the embedding model I rely on (required):

```bash
docker compose exec ollama ollama pull nomic-embed-text
```

If you're running the LLM locally with Ollama instead of Groq, pull that model too:

```bash
docker compose exec ollama ollama pull <model-name>
```

### Where to find things once it's running

| Service | URL |
|---|---|
| Web app | http://localhost:5173 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| ChromaDB | http://localhost:8001 |
| Solr | http://localhost:8983 |
| Kafka UI | http://localhost:8080 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

### Creating the first admin account

I haven't built a sign-up screen yet — on a fresh install you need to insert the
first `ADMIN` user directly into MongoDB (every account after that can be created
from my UI).

```bash
# 1. Hash a password
docker compose exec backend python -c "from app.security.password import hash_password; print(hash_password('YourPassword'))"

# 2. Open a Mongo shell
docker compose exec mongodb mongosh
```

```javascript
use YOUR_DB_NAME

db.counters.updateOne({ _id: "users" }, { $set: { sequence: 1 } }, { upsert: true })

db.users.insertOne({
  user_id: "USR-000001",
  first_name: "Admin",
  last_name: "User",
  email: "admin@snrt.ma",
  role: "ADMIN",
  status: "ACTIVE",
  password: "PASTE_THE_HASH_HERE",
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString()
})
```

Log in at `http://localhost:5173` with that email and password.

### Roles

| Role | Can do |
|---|---|
| `ADMIN` | Everything — dashboard, user management, upload, search |
| `DOCUMENTALIST` | Upload and search, no user management |
| `SNRT_USER` | Search only |

> New users get a default password (`123456`) for now — it was fine while I was
> testing, but it's on my to-do list to replace with a proper password-reset flow
> before this goes to production.

## Searching my archives

- **Keyword search** — best when you know a title, name, or exact phrase.
- **Semantic search** — finds related content even if the wording is different.
- **Ask a question (RAG)** — get a direct answer built from the most relevant
  passages in the archives. I'd still recommend double-checking the sources it cites.

## Monitoring

Prometheus scrapes metrics from my API and workers, Loki collects the logs, and
Grafana ties it all together in one dashboard I built
(`grafana/dashboards/snrt-monitoring.json`). Commands I use most often:

```bash
docker compose ps
docker compose logs -f document-worker
docker compose down   # stops everything, keeps my data
```

## A note on where this stands

This is still a work in progress on my end — password reset, production-hardening,
and a few extra features are next on my list. Feedback and issues are always welcome.

---

*Built by me, Fatiha Khassil, Student at ENSIAS, for SNRT.*
