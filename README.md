# Deplock

Deplock is a lightweight Coolify-like control plane for deploying projects to remote Docker hosts over SSH.

## Stack

- Backend: FastAPI + SQLAlchemy + SQLite
- Frontend: Vue 3 + Vite + Tailwind CSS
- Desktop shell: `pywebview`

## Important

- On Windows, the desktop app in this repository currently requires Python `3.13.x`.
- Python `3.14` is not supported here because the Windows `pywebview` backend depends on `pythonnet`, and that stack is not working with the current project setup on `3.14`.

## First Setup

```powershell
uv python install 3.13
uv venv --python 3.13
uv sync
npm install --prefix frontend
```

## Run Desktop

Build the frontend first, then start the desktop launcher:

```powershell
npm run build --prefix frontend
uv run main.py
```

The launcher starts FastAPI locally, waits for `/health`, and opens the UI in a `pywebview` window.

## Build Executable

```powershell
uv run python build.py
```

The build script:

- builds `frontend/dist`
- packages the desktop app with PyInstaller

The executable is created in `dist/`.

## Development Notes

- The backend serves the built frontend from `frontend/dist`, so after frontend changes you must rebuild it.
- Existing local SQLite databases with an older schema are patched on startup for missing dev columns like `servers.is_active` and `projects.use_https`.
- The tracked `deplock.db` should not be treated as authoritative project state.
