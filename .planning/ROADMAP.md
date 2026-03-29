# Project Roadmap

## Phase 1: WebSocket Backend Foundation (Alpaca streaming)
- Establish an `alpaca_stream.py` module (or integration in `mcp_server.py`/`orchestrator.py`) to connect to Alpaca's trade updates WS feed.
- Update `data_snapshots` asynchronously when Alpaca pushes a trade update, rather than only during polling intervals.
- Add robust auto-reconnection logic.

## Phase 2: UI Realtime Integration (Flask to React)
- Add Flask-SocketIO (or plain WebSocket / SSE) support inside `server.py` to push changes down to clients.
- Implement the hook inside `MiraiDashboard.jsx` to receive these pushes and directly mutate the existing React State (`positions`, `orders`).
- Add a subtle pulse/dot UI indicator showing connection status ("Live" / "Disconnected").

## Phase 3: Manual Trade Override Control
- Expose endpoints for `Cancel Order` (`DELETE /api/orders/<id>`) and ensure `POST /api/trade` is instantly executable.
- Modify `MiraiDashboard.jsx` to render functional "Cancel" buttons on working orders.
- Provide a responsive UI overlay/toast notifications when an order is updated successfully by the user.

## Future Phases
- Phase 4: Full Multi-Asset Support (Crypto/Options).
