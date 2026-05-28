# Backend Setup

## Local Database

The backend currently uses SQLite for low-cost local development:

```env
DATABASE_URL=sqlite+aiosqlite:///./ai_interview.db
```

The SQLite database file is created at:

```text
backend/ai_interview.db
```

## Start Server

From `backend/`:

```powershell
.\venv\Scripts\python.exe -m uvicorn apps.main:app --host 0.0.0.0 --port 1662 --reload
```

## View Tables

From `backend/`:

```powershell
.\venv\Scripts\python.exe -c "import sqlite3; con=sqlite3.connect('ai_interview.db'); print([row[0] for row in con.execute(\"select name from sqlite_master where type='table' order by name\")]); con.close()"
```

## Planned Services

- Ollama for local LLM question generation and evaluation.
- Sarvam AI for STT and TTS.
- ChromaDB for resume embeddings.
- Redis for cache, rate limiting, and session persistence.
- Alembic for production migrations.
