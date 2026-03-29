# Conventions

## Module Architecture
The system enforces strict boundary isolation:
`M1` (Data) -> `JSON` -> `M2` (AI) -> `JSON` -> `M3` (Trading).
Modules use raw `JSON` serialization/deserialization on disk (`backend/data_snapshots`) rather than in-memory message buses.

## UI Design Paradigm
- **Aesthetic**: Brutalist / Bloomberg Terminal styled interface. Monospaced font (`IBM Plex Mono`), `#0A0A0A` base background with sharp contrast (e.g. Neon Orange `#FF6600`).
- **State**: Unified React `useState` and `useEffect` hooks relying heavily on `setInterval` to fetch latest backend state objects from standard API endpoints inside a monolithic `MiraiDashboard.jsx`.
- **CSS**: Uses plain JS `style={{...}}` blocks.

## Naming & Typing
- **Python Variables**: Uses snake_case variables and CamelCase classes. Very light use of Type Hints.
- **REST Endpoints**: Simple verbs (`GET /api/market`). No dynamic routes/parameters mostly.

## Secret Management
- **Zero Hardcoding**: API keys (Alpaca, Groq, etc.) MUST NEVER be hardcoded.
- **Dotenv**: All credentials reside in a root `.env` file (git-ignored).
- **Initialization**: Every standalone Python module or service entry point must call `load_dotenv()` from the project root.
- **Examples**: Update `.env.example` when adding new required environment variables.

## Project Hygiene
- **Minimalist Workspace**: Delete diagnostic scripts (`diagnose.py`, `test_*.py`) once a feature is verified and stable.
- **Ignored Artifacts**: Runtime data (`data_snapshots/`), logs (`logs/`), and caches (`node_modules/`, `__pycache__/`) must be strictly excluded from version control via `.gitignore`.
- **GSD Workflow**: Planning artifacts (`.planning/`) are allowed and encouraged for state tracking but should not contain sensitive data.
