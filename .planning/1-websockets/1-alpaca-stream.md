---
description: Implement Alpaca WebSocket streaming
dependencies: []
---

# Phase 1: WebSocket Backend Foundation (Alpaca streaming)

## Objective
Establish a persistent WebSocket connection to Alpaca to listen for live trade and order updates, replacing the need to poll Alpaca heavily. Update the JSON `data_snapshots` instantly upon receiving these events.

## Steps
1. Create a new module `backend/alpaca_stream.py`.
2. Implement Alpaca's `Stream` client from `alpaca.data.live` or `alpaca.trading.stream` (the user is using paper trading, so use the correct base URL).
3. Connect and listen to the `trade_updates` channel.
4. When a `trade_update` event fires, grab the current order history JSON inside `data_snapshots\orders.json` and update/overwrite it instantly. (Or add to a queue).
5. Update `server.py` or `orchestrator.py` to launch this stream client asynchronously on server startup, ensuring it doesn't block Flask.

## Verification
- Run `server.py`.
- Place a mock trade directly via Alpaca's dashboard.
- Observe `orders.json` being mutated locally without needing a UI refresh or polling hit.
