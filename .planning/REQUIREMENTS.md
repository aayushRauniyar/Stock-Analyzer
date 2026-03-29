# Requirements

## Validated

- ✓ Basic UI monolithic implementation on React + Vite.
- ✓ Fetching real-time market data via `yfinance`.
- ✓ Generating AI signals via `groq` LLMs.
- ✓ Executing trades via `alpaca-trade-api`.

## Active

- [ ] **Alpaca WS to Backend**: Connect the Alpaca stream in Python to instantly trap trade/order events instead of pulling via REST.
- [ ] **Backend to Frontend WS/SSE**: Establish a real-time socket connection between Flask (`server.py`) and React (`MiraiDashboard.jsx`) to push Alpaca updates instantly.
- [ ] **Manual UI Trading Commands**: Implement UI controls to send manual Buy/Sell and Cancel signals through the API, overriding the orchestrator flow.
- [ ] **Resiliency**: Ensure the WebSocket auto-reconnects gracefully if the connection to Alpaca drops.
- [ ] Visual "live indicator" on the dashboard UI to show the WebSocket connection is actively streaming.

## Out of Scope

- Full DB Migration: Sticking to the established stateless JSON architecture for simplicity.
