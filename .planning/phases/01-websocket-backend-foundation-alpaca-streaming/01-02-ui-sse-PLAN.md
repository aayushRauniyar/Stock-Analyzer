---
id: 01-02
wave: 2
gap_closure: false
depends_on: ["01-01"]
files_modified: ["backend/server.py", "frontend/MiraiDashboard.jsx"]
autonomous: true
requirements: ["Backend to Frontend WS/SSE", "Manual UI Trading Commands", "Visual 'live indicator'"]
---

# Plan 01-02: React Dashboard SSE Updates

<objective>
To remove latency in the user dashboard by establishing a UI connection (EventStream/SSE via Flask Server) handling live Alpaca push updates forwarded from the `alpaca_stream.py` background process.
</objective>

## Tasks

### 1. Add Flask SSE / Socket listener Endpoint
<read_first>
- `backend/server.py`
</read_first>
<action>
Modify `backend/server.py` to add a new HTTP GET endpoint `/api/stream_order_events` utilizing Flask's `Response(generate(), mimetype='text/event-stream')` pattern. Create a global `queue.Queue` named `sse_queue` in the module. Have the SSE endpoint yield messages indefinitely from the Queue.
</action>
<acceptance_criteria>
- `backend/server.py` implements `/api/stream_order_events`.
- Endpoint returns `mimetype='text/event-stream'`.
- Code incorporates `queue` for threading.
</acceptance_criteria>

### 2. Inject order events into SSE Queue
<read_first>
- `backend/alpaca_stream.py`
- `backend/server.py`
</read_first>
<action>
In `backend/alpaca_stream.py`, whenever `on_trade_update` runs, fetch the `sse_queue` from `server` (or pass it in). Push the newly updated order JSON object to this `sse_queue` immediately after updating `orders.json`.
</action>
<acceptance_criteria>
- JSON is added to `queue.Queue` within the `alpaca_stream.py` loop.
</acceptance_criteria>

### 3. Connect React to Stream
<read_first>
- `frontend/MiraiDashboard.jsx`
</read_first>
<action>
In `frontend/MiraiDashboard.jsx`, initialize a new `EventSource('http://localhost:5000/api/stream_order_events')` inside a `useEffect` hook. Listen for messages. When an order message arrives, manually merge it into the existing `orders` state array and trigger an immediate re-render, overriding the polling interval behavior.
</action>
<acceptance_criteria>
- `EventSource` is used in `MiraiDashboard.jsx`.
- React state `setOrders` is updated in real time via the onmessage listener.
</acceptance_criteria>

### 4. Implement Manual UI Controls
<read_first>
- `frontend/MiraiDashboard.jsx`
- `backend/server.py`
- `backend/module3_trade_execution.py`
</read_first>
<action>
In `server.py`, add `app.route('/api/orders/<order_id>', methods=['DELETE'])` to wrap Alpaca's `api.cancel_order()`. In `MiraiDashboard.jsx`, add a "Cancel" text button specifically for working/pending orders in the 07 Orders tab that calls this endpoint. Also, add connection status text / green dot in the Dashboard header next to the clock indicating if `EventSource` is connected ("Live").
</action>
<acceptance_criteria>
- DELETE endpoint active on `/api/orders/<id>`.
- UI renders a clear UI status dot "● Live".
- Cancel buttons trigger UI API calls.
</acceptance_criteria>

<verification>
1. Launch Flask server and Dashboard. Status indicator shows "Live".
2. Buy AAPL via dashboard. Observe the SSE push updating the order to "filled" within 1 second instead of waiting 5 seconds.
3. Click "Cancel Order" on a pending order and see it disappear immediately.
</verification>

<must_haves>
- [ ] Establish a real-time socket connection between Flask (`server.py`) and React (`MiraiDashboard.jsx`) to push Alpaca updates instantly.
- [ ] Implement UI controls to send manual Buy/Sell and Cancel signals.
- [ ] Visual "live indicator" on the dashboard UI to show the WebSocket connection is actively streaming.
</must_haves>
