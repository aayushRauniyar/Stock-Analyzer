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
