# ForgeFlow

ForgeFlow is a local-first FastAPI/Jinja2 control plane for safe autonomous web-development runs. It persists users, projects, runs, events, test results, and validated checkpoints; generated projects are created under `WORKSPACE_ROOT`, never mixed into the control-plane source.

## Run

1. Copy `.env.example` to `.env`. Set a unique `SECRET_KEY`; optionally set `OPENROUTER_API_KEY` and an OpenRouter free model.
2. Create an environment and install: `python -m venv .venv`, then `.venv\Scripts\pip install -r requirements.txt` (Windows).
3. Start: `uvicorn app.main:app --reload`.
4. Visit `http://127.0.0.1:8000`, register, create a project, then submit the commerce requirement.

The first supported generated stack is a FastAPI web app with executable `pytest` API tests. It handles a commerce request and incremental “Add wishlist” request without replacing existing files. Start a completed generated demo from its workspace with `uvicorn backend.main:app --port 8001`.

## Safety model

All project file and terminal operations pass through `Guardrails`: resolved paths must stay in the project workspace; protected secret paths are denied; shell composition, destructive/network shell commands, and non-allowlisted commands are rejected; execution is time-limited; and `git push ... main` is blocked. Checkpoints are created only after executable tests pass. Remote pushes are opt-in and intentionally disabled by default.

## Architecture

- FastAPI + Jinja2 dashboard, authentication, JSON chat API and WebSocket activity stream.
- SQLAlchemy persistence (SQLite default for local MVP; PostgreSQL through `DATABASE_URL`).
- Supervisor workflow state, Developer agent, deterministic Tester, Git/checkpoint service.
- OpenRouter gateway isolated behind environment configuration; LLM output is never executed directly.
