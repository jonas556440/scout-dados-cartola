# ScoutDados AI Developer Instructions

## Architecture & Deployment
- **Stack:** FastAPI (Sync Monolith) + React 18 (Vite/SWC) + SQLite (WAL) + APScheduler.
- **Serving:** OpenLiteSpeed serves `frontend/dist` directly. **NEVER edit `dist/` manually.**
- **Deploy:** ALWAYS use `./deploy.sh` (frontend) or `./deploy.sh --full` (backend + frontend).
- **Paths:** Python scripts in root MUST start with the `sys.path.append(str(Path(__file__).parent))` hack.

## Backend Development (`api_server.py`)
- **Endpoints:** Define as **synchronous** `def` (not `async def`) due to blocking `requests` calls.
- **Patterns:** Use singleton instances (`api`, `mpv_calc`, `team_selector`) initialized at module level.
- **Failures:** Catch exceptions and raise `HTTPException`. Use 503 for external API failures.
- **Data Sync:** When changing data models, update these **three** synchronously:
  1. Pydantic model in `api_server.py` (e.g., `PlayerResponse`).
  2. Converter function in `api_server.py` (e.g., `converter_atleta_para_response`).
  3. TypeScript interface in `frontend/src/types/cartola.ts`.

## Frontend Development (`frontend/`)
- **Data/State:** NEVER use `fetch` directly. Use custom hooks in `src/hooks/useCartolaApi.ts` (React Query).
- **UI System:** Use `shadcn/ui` components in `src/components/ui`. Use `cn()` for class merging.
- **Branding:** App Name: "ScoutDados". Branding: Green/Dark. No generic "Cartola" titles.
- **Layout:** Pages export default, import `MainLayout`, and valid `<SEO>` tags.
- **Routing:** API proxy is configured in Vite; use `/api/...` relative paths in configuration.

## Analysis & Logic (`src/analysis/`)
- **Modules:** `MPVCalculator` (valorization), `TeamSelector` (optimization), `ScorePredictor` (Poisson/Hybrid).
- **Dependencies:** Analytical modules should remain pure Python classes without direct API/DB coupling where possible.

## Test & Verification
- **Backend:** `pytest tests/ -m smoke` for quick checks. `uvicorn api_server:app --reload`.
- **Frontend:** `cd frontend && bun test`.
- **Logs:** `sudo journalctl -u cartolafc-backend -f` for production logs.
