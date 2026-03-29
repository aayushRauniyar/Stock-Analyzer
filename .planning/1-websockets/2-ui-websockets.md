---
description: Implement Flask UI websockets and React updates
dependencies: ["1-alpaca-stream"]
---
# Phase 2: UI Realtime Integration (Flask to React)

## Objective
Establish a persistent WebSocket/SSE connection between the Flask backend (`server.py`) and the React dashboard (`MiraiDashboard.jsx`) to push Alpaca trade updates instantly down to the client.

## Steps
1. In `server.py`, establish a WebSocket Server (e.g. `Flask-SocketIO` if added to dependencies, or simpler EventStream SSE if we want to avoid new HTTP transports, but WS is preferred based on user reqs). We will use `websockets` or `flask-sock`.
2. Wrap the Flask app so it can accept real-time connections from `http://localhost:5173`.
3. In `MiraiDashboard.jsx`, initialize a WebSocket connection using the native `WebSocket` API. Listen for `message` events containing `"type": "ORDER_UPDATE"`.
4. Add a green/red visual dot in the `MiraiDashboard.jsx` header indicating active WS connection status.
5. In the backend `alpaca_stream.py` (which updates `orders.json`), configure it to ALSO emit a message directly to any connected `websockets` clients whenever an order triggers from Alpaca.

## Verification
- Load UI, ensure terminal says "Connected to Realtime."
- Submit an order on Alpaca website; the React frontend should repaint the `orders` table and `positions` instantly without user intervention.
