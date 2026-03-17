# AI LoL Predictor - Project Context & Guidelines

## 🚀 Overview
**AI LoL Predictor** (AI_LOL_Analist) is a full-stack application designed for League of Legends match analysis and prediction. It features a data processing pipeline, a FastAPI backend, and a modern Svelte 5 frontend.

## 🛠️ Tech Stack
- **Backend**: Python 3.x, FastAPI, Uvicorn, Pydantic, orjson.
- **Frontend**: Svelte 5 (Runes & Snippets), SvelteKit, TypeScript, TailwindCSS v4, Vite, Chart.js, GSAP.
- **Database**: SQLite (`data/db/lol_datamatches.db`) with a layered architecture (Silver/Gold/Platinum).
- **Testing**: Pytest (Backend), Vitest (Frontend), Hypothesis (Property-based testing).

## 📂 Key Directory Structure
- `api.py`: Main FastAPI entry point.
- `interface/`: Core business logic, services, and data providers.
- `pipeline/`: Data ingestion and transformation scripts (Medallion architecture).
- `frontend/src/`: SvelteKit application.
- `data/`: Local database and asset storage.
- `tests/`: Backend test suite.

## 📜 Development Standards & Conventions

### 🐍 Backend (Python/FastAPI)
- **Type Hinting**: Always use type hints for function signatures and Pydantic models.
- **Response Handling**: Use `orjson` for high-performance JSON serialization (configured in `api.py`).
- **Error Handling**: Use `HTTPException` for API-level errors.
- **Testing**: Maintain high coverage with Pytest and Hypothesis.

### ⚡ Frontend (Svelte 5 / TypeScript)
- **Svelte 5**: Use modern Svelte 5 features (Runes: `$state`, `$derived`, `$effect`; Snippets).
- **Styling**: TailwindCSS v4 is used. Follow utility-first patterns.
- **Charts**: Use `Chart.js` for data visualization.
- **State Management**: Keep state local or use Svelte 5's fine-grained reactivity.

### 🗄️ Database (SQLite)
- **Schema Management**: Follow the pipeline numbering (1-7) for data evolution.
- **Silver Layer**: Refined match data with unique constraints on `(gameid, participantid)`.
- **Naming**: Consistent snake_case for table and column names.

## 🔄 Workflow & Mandates
- **Environment**: All commands and scripts must be compatible with **Windows (PowerShell)**.
- **Commits**: As per global context, perform a **commit for each modified file individually** once a logical change is complete.
- **Commit Messages**: Detailed and written in **Portuguese (pt-BR)**.
- **Surgical Updates**: Prefer `replace` over `write_file` for large existing files.
- **Validation**: Always run relevant tests (Pytest/Vitest) after making changes.

## 💡 Project-Specific Tips
- The `pipeline/` scripts must be executed in order if resetting the data.
- Local champion images are served from `data/champs`.
- Team logos are lazily downloaded from Liquipedia if missing.
