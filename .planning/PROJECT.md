# Mirai ArcSphere Real-Time Sync

## What This Is
Upgrading the Mirai ArcSphere dashboard from a polling-based interface to a true, bi-directional, real-time trading terminal. It injects a low-latency pipeline to pipe Alpaca's execution streams directly into the React UI, while empowering the user with manual UI order control that overrides or supplements the AI.

## Core Value
Providing instant situational awareness and immediate interactive control without waiting for backend polling intervals, mimicking the feel of a premium, professional trading terminal like Bloomberg.

## Context
Currently, the Python backend writes AI signals and states to `data_snapshots\`, and the React frontend polls the Flask server to view the state. This creates latency, especially regarding filled Alpaca orders. We need to implement WebSockets (`backend/server.py` <-> `frontend/MiraiDashboard.jsx`) and connect Python to Alpaca's native WebSocket feeds to remove latency constraints.

## Requirements

### Validated
- ✓ Fetching real-time market data via `yfinance` (`module1_market_data.py`).
- ✓ Generating AI signals via `groq` LLMs (`module2_ai_analysis.py`).
- ✓ Executing trades via `alpaca-trade-api` (`module3_trade_execution.py`).
- ✓ Basic UI monolithic implementation on React + Vite.

### Active
- [ ] **Alpaca WS to Backend**: Connect the Alpaca stream in Python to instantly trap trade/order events instead of pulling via REST.
- [ ] **Backend to Frontend WS/SSE**: Establish a real-time socket or SSE connection between Flask (`server.py`) and React (`MiraiDashboard.jsx`).
- [ ] **Manual UI Trading Commands**: The dashboard needs to be able to send manual Buy/Sell and Cancel signals through the API, overriding the orchestrator flow.

### Out of Scope
- Full Postgres/DB migration — sticking to the established stateless JSON architecture for simplicity unless latency demands otherwise.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| WebSockets vs Polling | User mandated true real-time visibility. Polling will scale poorly and has high latency. | — Pending |
| Manual trading in UI | User wants full dashboard control, not just AI read-only views. | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-29 after initialization*
