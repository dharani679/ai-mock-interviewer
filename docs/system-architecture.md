# System Architecture

## Goal

Build an AI-powered mock interview platform where users can upload resumes, attend real-time AI interviews, speak with the interviewer, and receive structured feedback and analytics.

## High-Level Architecture

```text
React + Vite frontend
        |
        | REST + WebSocket
        v
FastAPI backend
        |
        | SQLAlchemy Async
        v
SQLite local database

FastAPI backend also talks to:
- Ollama for local LLM interview generation and evaluation
- Sarvam AI for speech-to-text and text-to-speech
- ChromaDB for resume embeddings and semantic retrieval
- Redis for caching, rate limiting, and session state
```

## Backend Layers

- `routers`: HTTP API endpoints.
- `websocket`: real-time interview sessions and transcript streaming.
- `services`: business logic such as interview flow, resume processing, and analytics.
- `repositories`: database access layer.
- `models`: SQLAlchemy ORM tables.
- `schemas`: Pydantic request and response models.
- `ai`: Ollama, Sarvam AI, prompt templates, and retrieval logic.
- `middleware`: auth, logging, rate limiting, and request context.
- `config`: environment-based application settings.
- `utils`: shared helpers.

## AI Flow

1. User creates an interview session.
2. Backend loads resume context and interview mode.
3. Backend asks Ollama to generate the first question.
4. User answers by text or voice.
5. Voice answers are sent to Sarvam AI STT.
6. Answer is stored and passed to Ollama for follow-up or evaluation.
7. AI feedback is stored in the database.
8. Analytics are updated for dashboards and trends.

## Voice Flow

```text
Browser microphone
  -> audio chunks
  -> FastAPI upload/WebSocket
  -> Sarvam AI STT
  -> transcript
  -> Ollama response
  -> Sarvam AI TTS
  -> browser audio playback
```

## Local Development Stack

- FastAPI API server
- SQLite database
- Ollama running locally
- Optional Redis and ChromaDB services
- React frontend dev server

## Production Path

The current local DB is SQLite because it is simple and low cost for development. The architecture keeps database access behind SQLAlchemy so the project can move to PostgreSQL later with Alembic migrations and a PostgreSQL `DATABASE_URL`.
