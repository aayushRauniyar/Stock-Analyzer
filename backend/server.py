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

from module1_market_data import (
    get_all_etf_data, get_market_data, is_market_open, get_market_schedule,
    get_sse_events, check_reanalysis_needed, update_global_watchlist
)
from module2_ai_analysis import analyse_all, analyse_ticker, get_cached_signals, should_reanalyse
from module3_trade_execution import get_account_info, get_open_positions, get_daily_loss, place_order, direct_place_order, get_trade_log
import db
from config import RiskLimits
import traceback
import sse_utils
import queue


# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(BASE_DIR, "data_snapshots", "latest_data.json")

app = Flask(__name__)
# Expanded CORS for more reliable dev sync
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": "*"}})

# SSE: Thread-safe subscribers imported from utils
sse_subscribers = sse_utils.sse_subscribers
sse_lock = sse_utils.sse_lock

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

# SSE broadcast logic moved to sse_utils.py
broadcast_sse = sse_utils.broadcast_sse


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


# ─────────────────────────────────────────────
# PHASE 3: TRADING ENDPOINTS
# ─────────────────────────────────────────────

@app.route("/api/positions", methods=["GET"])
def api_positions():
    """Return current open positions with entry, current price, P&L."""
    try:
        from module3_trade_execution import get_open_positions
        positions = get_open_positions()
        return jsonify({
            "positions": positions,
            "count": len(positions),
            "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
    except Exception as e:
        print(f"❌ ERROR in /api/positions: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/portfolio", methods=["GET"])
def api_portfolio():
    """Return account summary: equity, cash, buying power, P&L."""
    try:
        from module3_trade_execution import get_account_info, get_open_positions, get_daily_loss
        
        account = get_account_info()
        positions = get_open_positions()
        daily_loss = get_daily_loss()
        
        # Default account if Alpaca fetch fails
        if not account or not isinstance(account, dict):
            account = { "equity": 0, "cash": 0, "buying_power": 0, "unrealized_pl": 0 }
            
        equity = account.get("equity") or 0
        pnl_pct = (daily_loss / equity * 100) if equity > 0 else 0
        
        return jsonify({
            "account": account,
            "positions_count": len(positions),
            "daily_loss": daily_loss,
            "daily_loss_limit": RiskLimits.DAILY_MAX_LOSS_PCT,
            "daily_loss_pct": pnl_pct,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
    except Exception as e:
        print(f"❌ ERROR in /api/portfolio: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/tax-log", methods=["GET"])
def api_tax_log():
    """Return trade log (CSV format or JSON list)."""
    try:
        from module3_trade_execution import get_trade_log
        
        trades = get_trade_log()
        format_type = request.args.get("format", "json")
        
        if format_type == "csv":
            import csv
            from io import StringIO
            
            if not trades:
                return "", 204
            
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=trades[0].keys())
            writer.writeheader()
            writer.writerows(trades)
            
            return output.getvalue(), 200, {
                "Content-Type": "text/csv",
                "Content-Disposition": "attachment; filename=trade_log.csv"
            }
        else:
            return jsonify({
                "trades": db.get_trade_log(),
                "count": len(trades),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
    except Exception as e:
        print(f"❌ ERROR in /api/tax-log: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/api/auto-trade/enable", methods=["POST"])
def api_enable_auto_trade():
    """Toggle auto-trading on/off (user control)."""
    try:
        from module3_trade_execution import toggle_auto_trading, is_auto_trading_enabled
        
        data = request.get_json() or {}
        enabled = data.get("enabled")
        
        if enabled is None:
            # Toggle if not specified
            current = is_auto_trading_enabled()
            enabled = not current
        
        toggle_auto_trading(enabled)
        
        return jsonify({
            "auto_trading_enabled": enabled,
            "status": "🟢 AUTO-TRADING ENABLED" if enabled else "🔴 AUTO-TRADING DISABLED",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/watchlist", methods=["GET"])
def api_get_watchlist():
    """Return the current favorites watchlist from SQLite."""
    return jsonify({"watchlist": db.get_watchlist()})

@app.route("/api/watchlist/add", methods=["POST"])
def api_add_to_watchlist():
    """Add a ticker to the favorites watchlist."""
    data = request.get_json() or {}
    ticker = data.get("ticker", "").upper().strip()
    if not ticker: return jsonify({"error": "No ticker provided"}), 400
    
    current = db.get_watchlist()
    if ticker not in current:
        db.add_to_watchlist(ticker)
        update_global_watchlist()
        # Trigger a background fetch for the new ticker
        threading.Thread(target=get_market_data, args=(ticker,), daemon=True).start()
    
    return jsonify({"success": True, "watchlist": db.get_watchlist()})

@app.route("/api/watchlist/remove", methods=["POST"])
def api_remove_from_watchlist():
    """Remove a ticker from the favorites watchlist."""
    data = request.get_json() or {}
    ticker = data.get("ticker", "").upper().strip()
    if not ticker: return jsonify({"error": "No ticker provided"}), 400
    
    current = db.get_watchlist()
    if ticker in current:
        db.remove_from_watchlist(ticker)
        update_global_watchlist()
    
    return jsonify({"success": True, "watchlist": db.get_watchlist()})

@app.route("/api/orders", methods=["GET"])
def api_orders():
    """Return recent orders from SQLite DB (synced with Alpaca)."""
    try:
        limit = request.args.get("limit", 50, type=int)
        orders = db.get_orders(limit=limit)
        return jsonify({"orders": orders})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/orders/<order_id>", methods=["DELETE"])
def api_cancel_order(order_id):
    """Cancel a pending/working order."""
    try:
        from module3_trade_execution import get_api
        api = get_api()
        api.cancel_order(order_id)
        return jsonify({"success": True, "message": f"Order {order_id} cancelled"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/trade", methods=["POST"])
def api_trade():
    """Execute a trade (manual or AI-sized)."""
    try:
        from module3_trade_execution import place_order, direct_place_order, get_market_data as get_mkt
        
        data = request.get_json() or {}
        ticker = data.get("ticker", "").upper()
        side = data.get("side", "").lower()
        qty = data.get("qty")
        auto_size = data.get("auto_size", False)
        
        if not ticker or not side:
            return jsonify({"error": "Missing ticker or side"}), 400
        
        if auto_size:
            # Use strict ATR-based sizing (Phases 1-3 logic)
            mkt_data = get_mkt(ticker)
            sig = {"signal": "BUY" if side == "buy" else "SELL", "conf": 75, "reason": "Manual UI Trigger"}
            order_id = place_order(ticker, 0, side, sig, mkt_data)
        else:
            # Direct manual execution
            if not qty or int(qty) <= 0:
                return jsonify({"error": "Quantity required for manual trade"}), 400
            order_id = direct_place_order(ticker, int(qty), side)
        
        if order_id:
            return jsonify({"success": True, "order_id": order_id, "ticker": ticker, "side": side})
        else:
            return jsonify({"error": "Order execution failed"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/api/orchestrator-status", methods=["GET"])
def api_orchestrator_status():
    """Get orchestrator status: is it running, what are the signals, etc."""
    try:
        from orchestrator import get_orchestrator_status, is_auto_trading_enabled
        
        status = get_orchestrator_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stream", methods=["GET"])
def api_stream():
    """Server-Sent Events endpoint for real-time updates from Module 1 WebSocket."""
    def event_stream():
        q = queue.Queue(maxsize=50)
        with sse_lock:
            sse_subscribers.append(q)
        
        try:
            # Send initial heartbeat
            yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'time': datetime.now().isoformat()})}\n\n"

            while True:
                # Check Module 1's SSE queue for price updates
                module1_events = get_sse_events(timeout=1.0)
                for evt in module1_events:
                    # Check if re-analysis is needed
                    if evt.get("should_reanalyse"):
                        ticker = evt.get("ticker")
                        market_data = get_market_data(ticker)
                        signals = analyse_ticker(market_data)
                        evt["signal"] = signals  # Attach AI signal to event
                    
                    # Broadcast to client
                    try:
                        q.put_nowait(f"event: update\ndata: {json.dumps(evt, default=str)}\n\n")
                    except queue.Full:
                        pass
                
                # Also check for messages from /api/refresh
                try:
                    message = q.get(timeout=1.0)
                    yield message
                except queue.Empty:
                    # Send periodic heartbeat
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
    # Initialize SQLite Database for a Fresh Start
    db.init_db()
    
    print("=" * 56)
    print("  🌸 MIRAI ARCSPHERE · Backend API Server (with Orchestrator)")
    print("=" * 56)
    print(f"  API:         http://localhost:5000/api/")
    print(f"  Stream:      http://localhost:5000/api/stream")
    print(f"  Data:        {DATA_FILE}")
    print("=" * 56)

    # Start background scheduler in a separate thread
    scheduler_thread = threading.Thread(target=background_scheduler, daemon=True)
    scheduler_thread.start()

    # Start Alpaca order stream in a separate thread
    try:
        import alpaca_stream
        stream_thread = threading.Thread(target=alpaca_stream.start_stream, daemon=True)
        stream_thread.start()
    except Exception as e:
        print(f"⚠ Warning: Could not start Alpaca stream: {e}")

    # Start orchestrator in a separate thread
    try:
        from orchestrator import run_orchestrator
        orchestrator_thread = threading.Thread(target=run_orchestrator, daemon=True)
        orchestrator_thread.start()
    except Exception as e:
        print(f"⚠ Warning: Could not start orchestrator: {e}")

    # Start Flask server
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
