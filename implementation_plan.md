# Mirai ArcSphere — Full Rebuild Plan

## Goal

Rebuild the Mirai ArcSphere automated trading assistant with a clean, modular architecture and **real-time data streaming**. Price updates flow automatically from Alpaca WebSocket → Python backend → dashboard via Server-Sent Events (SSE). AI re-analysis triggers automatically on significant price moves (>1%).

## Build Order

```text
Module 1 → Module 2 → Module 4 (partial) → Module 3
  Data        AI         Dashboard             Trade
 (eyes)    (brain)        (face)              (hands)
```

---

## Real-Time Architecture

```text
┌─── Alpaca WebSocket ───┐    ┌─── Python Backend ───┐    ┌─── React Dashboard ──┐
│ Live price bars for    │───▶│ server.py            │───▶│ MiraiDashboard.jsx   │
│ SPY, QQQ, VTI          │    │  ├ receives prices   │SSE │  ├ EventSource /api/ │
│ (real-time stream)     │    │  ├ updates JSON      │    │  │   stream          │
└────────────────────────┘    │  ├ if move >1%:      │    │  ├ auto-updates cards│
                              │  │  trigger Module 2 │    │  └ no manual refresh │
┌─── Alpaca Historical ──┐    │  │  (AI re-analysis) │    │    needed            │
│ 90-day history for     │───▶│  └ serves REST API   │    └──────────────────────┘
│ indicator calculation  │    └────────────────────────┘
└────────────────────────┘
```

---

## Project Structure (Final)

```text
Stock Analyzer/
├── backend/
│   ├── server.py                   [NEW]  ← Flask API serving all modules
│   ├── module1_market_data.py      [MOVE] ← Cleaned up from root (Alpaca only)
│   ├── module2_ai_analysis.py      [NEW]  ← Groq AI signal engine (Llama 3)
│   ├── module3_trade_execution.py  [NEW]  ← Alpaca trade + risk + tax
│   └── requirements.txt            [NEW]  ← Unified Python deps
├── frontend/
│   ├── index.html                  [MOVE] ← Vite entry
│   ├── main.jsx                    [MOVE] ← React mount
│   ├── vite.config.js              [MOVE] ← Vite config with API proxy
│   ├── package.json                [MOVE]
│   └── MiraiDashboard.jsx          [MOVE] ← Rewritten to call API
├── data_snapshots/                 (as-is)
├── logs/                           (as-is)
└── README.md
```

---

## Proposed Changes

### Module 1: Market Data Engine (Eyes)

> [!NOTE]
> Module 1 is being upgraded to a unified Alpaca pipeline to prevent data mismatch between historical indicators and live execution.

#### [MOVE] module1_market_data.py
- Move to `backend/module1_market_data.py`
- Fix paths for `backend/` location
- **Update Data Source**: Replace `yfinance` with **Alpaca Historical API** for the 90-day lookback used to calculate RSI/MACD.
- **Add WebSocket streaming**: `start_live_stream()` subscribes to Alpaca bar data for SPY/QQQ/VTI.
- On each new bar: update `latest_data.json`, push event to `server.py` subscribers.
- Falls back to scheduled polling (every 60 min) if WebSocket unavailable.

---

### Module 2: AI Analysis Engine (Brain)

#### [NEW] backend/module2_ai_analysis.py
- Takes market data dict from Module 1, sends to Groq API via `groq` SDK for ultra-fast, free inference.
- Returns structured JSON: `{ signal, conf, risk, entry, exit, stop, tf, reason, risks[] }`
- **Auto-triggered** when price moves >1% from last analysis
- Caches results to avoid duplicate API calls (re-analyses only when data changes significantly)
- Functions:
  - `analyse_ticker(ticker_data: dict) → dict` — single ticker
  - `analyse_all(all_data: dict) → dict` — all tickers
  - `get_cached_signals() → dict` — returns last signals without re-calling API
  - `should_reanalyse(old_data, new_data) → bool` — checks if price moved enough

---

### Backend API Server

#### [NEW] backend/server.py
- Flask server with **REST + Server-Sent Events (SSE)**:
  - `GET /api/market-data` → returns latest snapshot
  - `GET /api/stream` → **SSE endpoint** — pushes live price updates to the dashboard in real-time
  - `POST /api/refresh` → triggers Module 1 fresh fetch + Module 2 analysis
  - `GET /api/signals` → returns cached AI signals
  - `GET /api/positions` → returns positions (Module 3)
  - `GET /api/portfolio` → returns portfolio summary (Module 3)
  - `POST /api/trade` → executes a trade (Module 3)
  - `GET /api/tax-log` → returns tax log (Module 3)
- **Real-time flow**: Module 1 WebSocket → internal queue → SSE → browser
- CORS enabled for local Vite dev server

---

### Module 4: Dashboard UI (Face) — Partial

#### [MODIFY] MiraiDashboard.jsx
- **Remove** `callClaude()` — all AI calls go through the backend now
- **Add `EventSource('/api/stream')`** — listens for real-time price pushes via SSE
- **Replace** `fetchAll()` with call to `/api/market-data` + `/api/signals`
- **Remove** `transformTicker()` — backend returns dashboard-ready format
- **Keep** all UI/theme/component code (it works and looks great)
- **Add live update indicator** — pulsing dot when stream is active
- Cards update automatically as new prices arrive — no manual refresh needed

#### [MODIFY] vite.config.js
- Add proxy: `/api` → `http://localhost:5000` (Flask backend)

---

### Module 3: Trade Execution Engine (Hands) — Last

#### [NEW] backend/module3_trade_execution.py
- Connects to Alpaca paper trading API
- Functions:
  - `place_order(ticker, qty, side)` — buy/sell
  - `get_positions()` → current open positions
  - `get_portfolio()` → account value, P&L, cash
  - `calculate_position_size(equity, risk_pct, entry, stop)` — risk management
  - `check_risk_limits(account)` — daily loss limit check
  - `log_trade(...)` — writes to `trade_log.csv` for ATO tax records
- All trades logged with timestamp, reasoning, and AI confidence

#### [NEW] backend/requirements.txt
```text
# Unified dependencies for all modules
ta>=0.11.0
pandas>=2.0.0
numpy>=1.24.0,<2.0.0
schedule>=1.2.0
pytz>=2024.1
alpaca-trade-api>=3.0.2
pyarrow>=16.0.0
flask>=3.0.0
flask-cors>=4.0.0
groq>=0.4.0
```

---

## What Gets Deleted/Cleaned Up

| File | Action |
|---|---|
| `demo-dashboard/` | Delete — was a failed Vite subfolder attempt |
| Root `requirements_module1.txt` | Replace with unified `backend/requirements.txt` |
| Root `module1_market_data.py` | Move to `backend/` |
| Root `MiraiDashboard.jsx` | Move to `frontend/` |
| Root `main.jsx`, `index.html`, `vite.config.js` | Move to `frontend/` |
| Root `package.json`, `package-lock.json`, `node_modules` | Move to `frontend/` |

---

## Verification Plan

### Module 1
```powershell
cd backend
python module1_market_data.py test
# ✅ Should print SPY data with real prices via Alpaca
```

### Module 2
```powershell
cd backend
python module2_ai_analysis.py test
# ✅ Should print BUY/SELL/HOLD signal for SPY with reasoning via Groq
```

### Backend API
```powershell
cd backend
python server.py
# Then in another terminal:
curl http://localhost:5000/api/market-data
# ✅ Should return JSON with SPY, QQQ, VTI data
```

### Dashboard (Module 4)
```powershell
cd frontend
npx vite --port 5173
# Open [http://127.0.0.1:5173/](http://127.0.0.1:5173/)
# Click "🌸 Refresh All"
# ✅ Prices update with real data, AI signals appear
```

### Module 3
```powershell
cd backend
python module3_trade_execution.py test
# ✅ Should show paper account status and test position sizing
```