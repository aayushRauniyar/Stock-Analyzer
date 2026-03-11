"""
╔══════════════════════════════════════════════════════════╗
║     MIRAI ARCSPHERE · 未来アークスフィア                   ║
║     Backend API Server                                   ║
║     Version: 1.0.0                                       ║
║     Status:  ✅ Active                                   ║
╚══════════════════════════════════════════════════════════╝

PURPOSE:
  Flask API server that bridges the Python backend modules
  with the React frontend dashboard. Includes REST endpoints
  and Server-Sent Events (SSE) for real-time data streaming.

ENDPOINTS:
  GET  /api/market-data  → latest ETF snapshot
  GET  /api/signals      → cached AI signals
  POST /api/refresh      → trigger fresh data fetch + AI analysis
  GET  /api/stream       → SSE stream for real-time updates

USAGE:
  python server.py
"""

import os
import sys
import json
import time
import queue
import threading
from datetime import datetime

from flask import Flask, jsonify, request, Response
from flask_cors import CORS

# Add backend directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from module1_market_data import get_all_etf_data, get_market_data, is_market_open, get_market_schedule
from module2_ai_analysis import analyse_all, analyse_ticker, get_cached_signals, should_reanalyse

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data_snapshots", "latest_data.json")

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# SSE: Thread-safe queue for broadcasting events to all connected clients
sse_subscribers = []
sse_lock = threading.Lock()


# ─────────────────────────────────────────────
# HELPER: Transform data for dashboard format
# ─────────────────────────────────────────────

def transform_for_dashboard(raw: dict) -> dict:
    """Convert Module 1 output fields to dashboard-expected field names."""
    return {
        "ticker": raw.get("ticker"),
        "price": raw.get("price"),
        "prev": raw.get("prev_close"),
        "chg": raw.get("daily_change_pct"),
        "rsi": raw.get("rsi"),
        "macd": raw.get("macd_signal", "NEUTRAL"),
        "bb": raw.get("bb_signal", "NEUTRAL"),
        "sma20": "ABOVE" if raw.get("above_sma20") else "BELOW",
        "sma50": "ABOVE" if raw.get("above_sma50") else "BELOW",
        "hi52": raw.get("bb_upper"),
        "lo52": raw.get("bb_lower"),
        "vol": raw.get("volume"),
    }


# ─────────────────────────────────────────────
# HELPER: SSE broadcast
# ─────────────────────────────────────────────

def broadcast_sse(event_type: str, data: dict):
    """Push an event to all connected SSE clients."""
    message = f"event: {event_type}\ndata: {json.dumps(data, default=str)}\n\n"
    with sse_lock:
        dead = []
        for i, q in enumerate(sse_subscribers):
            try:
                q.put_nowait(message)
            except queue.Full:
                dead.append(i)
        # Remove dead subscribers
        for i in reversed(dead):
            sse_subscribers.pop(i)


# ─────────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────────

@app.route("/api/market-data", methods=["GET"])
def api_market_data():
    """Return the latest market data snapshot, transformed for the dashboard."""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                snapshot = json.load(f)

            # Transform each ticker for the dashboard
            transformed = {}
            for ticker, data in snapshot.get("data", {}).items():
                transformed[ticker] = transform_for_dashboard(data)

            return jsonify({
                "fetched_at": snapshot.get("fetched_at"),
                "fetched_at_aest": snapshot.get("fetched_at_aest"),
                "market_open": snapshot.get("market_open"),
                "data": transformed,
            })
        else:
            return jsonify({"error": "No data available. Run Module 1 first."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/signals", methods=["GET"])
def api_signals():
    """Return the cached AI signals."""
    cache = get_cached_signals()
    if cache:
        return jsonify(cache)
    return jsonify({"error": "No cached signals. Click Refresh to generate."}), 404


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    """Trigger a fresh data fetch (Module 1) + AI analysis (Module 2)."""
    try:
        # Step 1: Fetch fresh market data
        all_data = get_all_etf_data()

        # Step 2: Run AI analysis on the fresh data
        signals = analyse_all(all_data)

        # Transform for dashboard
        transformed = {}
        for ticker, data in all_data.items():
            transformed[ticker] = transform_for_dashboard(data)

        result = {
            "market_data": transformed,
            "signals": signals,
            "refreshed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "market_open": is_market_open(),
        }

        # Broadcast to SSE subscribers
        broadcast_sse("refresh", result)

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/market-status", methods=["GET"])
def api_market_status():
    """Return current market open/close status and schedule."""
    try:
        schedule = get_market_schedule()
        return jsonify(schedule)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stream", methods=["GET"])
def api_stream():
    """Server-Sent Events endpoint for real-time updates."""
    def event_stream():
        q = queue.Queue(maxsize=50)
        with sse_lock:
            sse_subscribers.append(q)
        try:
            # Send initial heartbeat
            yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'time': datetime.now().isoformat()})}\n\n"

            while True:
                try:
                    message = q.get(timeout=30)  # 30s heartbeat
                    yield message
                except queue.Empty:
                    # Send heartbeat to keep connection alive
                    yield f"event: heartbeat\ndata: {json.dumps({'time': datetime.now().isoformat()})}\n\n"
        except GeneratorExit:
            with sse_lock:
                if q in sse_subscribers:
                    sse_subscribers.remove(q)

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


# ─────────────────────────────────────────────
# BACKGROUND: Auto-refresh during market hours
# ─────────────────────────────────────────────

def background_scheduler():
    """Background thread that auto-refreshes data during market hours."""
    import schedule as sched

    def auto_cycle():
        if not is_market_open():
            return
        print("[AUTO] Market is open — running data cycle...")
        all_data = get_all_etf_data()

        # Check if we need re-analysis
        cached = get_cached_signals()
        cached_signals = cached.get("signals", {})
        needs_analysis = False

        for ticker, data in all_data.items():
            old = cached_signals.get(ticker, {})
            if should_reanalyse(old, data):
                needs_analysis = True
                break

        if needs_analysis:
            signals = analyse_all(all_data)
        else:
            signals = cached_signals

        # Transform and broadcast
        transformed = {}
        for ticker, data in all_data.items():
            transformed[ticker] = transform_for_dashboard(data)

        broadcast_sse("update", {
            "market_data": transformed,
            "signals": signals,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    # Run every 5 minutes during market hours
    sched.every(5).minutes.do(auto_cycle)

    while True:
        sched.run_pending()
        time.sleep(30)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 56)
    print("  🌸 MIRAI ARCSPHERE · Backend API Server")
    print("=" * 56)
    print(f"  API:     http://localhost:5000/api/")
    print(f"  Stream:  http://localhost:5000/api/stream")
    print(f"  Data:    {DATA_FILE}")
    print("=" * 56)

    # Start background scheduler in a separate thread
    scheduler_thread = threading.Thread(target=background_scheduler, daemon=True)
    scheduler_thread.start()

    # Start Flask server
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
