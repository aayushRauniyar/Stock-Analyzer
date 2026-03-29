---
id: 01-01
wave: 1
gap_closure: false
depends_on: []
files_modified: ["backend/alpaca_stream.py", "backend/server.py", "backend/orchestrator.py"]
autonomous: true
requirements: ["Alpaca WS to Backend", "Resiliency"]
---

# Plan 01-01: Alpaca WebSocket Stream

<objective>
Establish a WebSocket connection to Alpaca to listen for live trade and order updates, replacing the need to poll Alpaca heavily. Update the JSON `data_snapshots\orders.json` instantly upon receiving these events.
</objective>

## Tasks

### 1. Create Alpaca Stream Client
<read_first>
- `backend/module3_trade_execution.py`
- `backend/config.py`
</read_first>
<action>
Create a new file `backend/alpaca_stream.py`. Instantiate `alpaca.trading.stream.TradingStream` using `config.ALPACA_API_KEY`, `config.ALPACA_SECRET_KEY`, and `paper=True`. Add a basic callback for `trade_updates` that prints the update to the console. Include auto-reconnection logic using `try-except` blocks around the stream consumer.
</action>
<acceptance_criteria>
- `backend/alpaca_stream.py` is created.
- File contains `TradingStream` initialization.
- File contains `async def on_trade_update(data)` callback.
</acceptance_criteria>

### 2. Update orders.json on Trade Event
<read_first>
- `backend/alpaca_stream.py`
- `backend/server.py`
</read_first>
<action>
Modify `alpaca_stream.py`. In `on_trade_update`, parse the incoming Alpaca order event. Load `backend/data_snapshots/orders.json`, append or update the matched order using its `id`, and write it back to disk. Use `filelock` or a basic threading lock to prevent corruption of the JSON file during concurrent writes by other modules.
</action>
<acceptance_criteria>
- `backend/alpaca_stream.py` imports `json`.
- Event callback successfully opens and overwrites `backend/data_snapshots/orders.json`.
</acceptance_criteria>

### 3. Start stream asynchronously
<read_first>
- `backend/server.py`
- `backend/alpaca_stream.py`
</read_first>
<action>
Modify `backend/server.py`. Import the `start_stream` function from `alpaca_stream.py`. In the `__main__` block, spawn a dedicated background thread `threading.Thread(target=start_stream, daemon=True).start()` just before `app.run()`.
</action>
<acceptance_criteria>
- `backend/server.py` imports `alpaca_stream`.
- Server uses `threading.Thread` to bootstrap the websocket listener.
</acceptance_criteria>

<verification>
1. Run `python backend/server.py`.
2. Server launches successfully and background thread prints "Listening to Alpaca".
</verification>

<must_haves>
- [ ] Connect the Alpaca stream in Python to instantly trap trade/order events instead of pulling via REST.
- [ ] Ensure the WebSocket auto-reconnects gracefully if the connection drops.
</must_haves>
