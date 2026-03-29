# Architecture

## Core Pattern
- **Three-Module System (Pipeline)**
  - `module1_market_data.py`: Pulls realtime price data and calculates Technical Analysis metrics.
  - `module2_ai_analysis.py`: Consumes indicator outputs from Module 1, producing buy/sell/hold confidence ratings via LLMs.
  - `module3_trade_execution.py`: Reads signals and generates/calculates target trade positions according to ATR models, sending valid orders out.
  - `orchestrator.py`: Joins M1, M2, and M3 sequentially.

## Data Flow
- `orchestrator.py` is invoked periodically by `schedule` or `/api/trade` requests via `server.py`.
- Module outputs are written as flat JSON snapshots in `backend/data_snapshots/` to act as a system-state DB.
- UI layer (`MiraiDashboard.jsx`) polls Flask (`server.py`) which reads snapshot files into memory.

## Web Server
- `backend/server.py`: Flask application exposing API endpoints:
  - `GET /api/market`: Fetch `market_data.json`
  - `GET /api/signals`: Fetch `ai_signals.json`
  - `POST /api/trade`: Manual endpoint overriding the orchestrator
  - `/api/watchlist`: Fetch/manipulate a local `watchlist.json`
