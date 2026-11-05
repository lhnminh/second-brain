# Frontend

`dashboard.py` serves the dashboard and `dev.py` serves a read-only developer console through the same FastAPI origin. No separate frontend build or Node installation is needed. See the [root README](../README.md) to run the app.

- Short-term work sorts by deadline. Lists scroll after five tasks; long-term goals occupy the right panel. Task bubbles open expanded details below.
- Task names, dates and subtasks are editable. Importance and focus live in Edit task. Completion history separates short- and long-term work; trash supports Undo.
- Talk to Muse opens General chat. Ask Muse and eligible handoffs open a larger task conversation; subtasks share their root's history. Handoff is limited to suitable short-term work.
- Enter sends; Shift+Enter inserts a newline. Input grows from one to six lines. Voice fills an editable draft; the paperclip offers PDF, TXT, Word and image uploads.
- A quiet Example workspace label identifies starter content. Sample context is explicitly labeled; assistant responses are never fabricated.
- `/dev` helps inspect real model requests, saved objects and change events. It uses the same workspace identity and has no app logo.

[Design direction](DESIGN.md) · [API contract](../API_CONTRACT.md)
