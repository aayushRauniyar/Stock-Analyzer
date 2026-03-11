# Mirai ArcSphere — Rebuild Task List

## Phase 1: Project Restructure
- [ ] Create `backend/` and `frontend/` directories
- [ ] Move [module1_market_data.py](file:///e:/Projects%20Manu/Stock%20Analyzer/module1_market_data.py) → `backend/`
- [ ] Move [MiraiDashboard.jsx](file:///e:/Projects%20Manu/Stock%20Analyzer/MiraiDashboard.jsx), [main.jsx](file:///e:/Projects%20Manu/Stock%20Analyzer/main.jsx), [index.html](file:///e:/Projects%20Manu/Stock%20Analyzer/index.html), [vite.config.js](file:///e:/Projects%20Manu/Stock%20Analyzer/vite.config.js), [package.json](file:///e:/Projects%20Manu/Stock%20Analyzer/package.json) → `frontend/`
- [ ] Delete `demo-dashboard/` folder
- [ ] Create unified `backend/requirements.txt`
- [ ] Update paths in moved files

## Phase 2: Module 1 — Market Data Engine (Eyes)
- [ ] Fix [module1_market_data.py](file:///e:/Projects%20Manu/Stock%20Analyzer/module1_market_data.py) paths for `backend/` location
- [ ] Verify `python module1_market_data.py test` still works

## Phase 3: Module 2 — AI Analysis Engine (Brain)
- [ ] Create `backend/module2_ai_analysis.py`
- [ ] Implement `analyse_ticker()` with Claude API
- [ ] Implement `analyse_all()` and `get_cached_signals()`
- [ ] Verify `python module2_ai_analysis.py test`

## Phase 4: Backend API Server
- [ ] Create `backend/server.py` (Flask)
- [ ] Implement `/api/market-data`, `/api/refresh`, `/api/signals` endpoints
- [ ] Verify API returns correct data

## Phase 5: Module 4 — Dashboard UI (Face)
- [ ] Update [vite.config.js](file:///e:/Projects%20Manu/Stock%20Analyzer/vite.config.js) with API proxy to Flask
- [ ] Rewrite `fetchAll()` and `fetchSignal()` to call backend API
- [ ] Remove [callClaude()](file:///e:/Projects%20Manu/Stock%20Analyzer/MiraiDashboard.jsx#37-51) from frontend
- [ ] Verify dashboard renders with real data from backend

## Phase 6: Module 3 — Trade Execution Engine (Hands)
- [ ] Create `backend/module3_trade_execution.py`
- [ ] Implement Alpaca integration (paper trading)
- [ ] Implement risk management and tax logging
- [ ] Add `/api/positions`, `/api/portfolio`, `/api/trade`, `/api/tax-log` endpoints
- [ ] Verify paper trade execution
