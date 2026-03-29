import json
import logging
import asyncio
import os
import threading
import time
from datetime import datetime
from alpaca.trading.stream import TradingStream
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from config import ALPACA_API_KEY, ALPACA_SECRET_KEY
import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AlpacaStream")

def update_db_from_trade_update(trade_update):
    """
    Update the SQLite database and broadcast SSE when a trade execution occurs.
    """
    try:
        order = trade_update.order
        order_id = str(order.id)
        status = order.status.value if hasattr(order.status, 'value') else str(order.status)
        filled_qty = int(order.filled_qty) if order.filled_qty else 0
        avg_price = float(order.filled_avg_price) if order.filled_avg_price else None
        
        logger.info(f"🔄 Syncing Order {order_id} ({order.symbol}) -> Status: {status} | Filled: {filled_qty}")

        # Update SQLite
        db.update_order_status(order_id, status, filled_qty, avg_price)
        
        # If filled, also add to trade log (Tax Log)
        if status == "filled":
            db.add_to_trade_log(
                ticker=order.symbol,
                action=order.side.value if hasattr(order.side, 'value') else str(order.side),
                qty=filled_qty,
                price=avg_price or 0,
                reason=f"Alpaca {trade_update.event} update"
            )

        # Prepare SSE data for real-time UI updates
        order_data = {
            "id": order_id,
            "symbol": order.symbol,
            "qty": str(order.qty),
            "filled_qty": str(filled_qty),
            "status": status,
            "event": trade_update.event,
            "timestamp": datetime.now().isoformat() if 'datetime' in globals() else str(time.time())
        }

        # Broadcast SSE via utils to prevent circular dependency
        from sse_utils import broadcast_sse
        try:
            broadcast_sse("order_update", order_data)
        except Exception as e:
            # Server might not be running or import fails in some contexts
            logger.error(f"⚠ SSE broadcast failed: {e}")

    except Exception as e:
        logger.error(f"Failed to update database from trade update: {e}")

async def trade_update_handler(data):
    """
    Callback fired by Alpaca when an order fills, cancels, etc.
    """
    logger.info(f"Trade update received: {data.event}")
    update_db_from_trade_update(data)

def run_stream():
    """
    Blocking call to start the Alpaca TradingStream.
    """
    logger.info("Starting Alpaca Trading Stream...")
    try:
        stream = TradingStream(
            api_key=ALPACA_API_KEY,
            secret_key=ALPACA_SECRET_KEY,
            paper=True
        )
        stream.subscribe_trade_updates(trade_update_handler)
        stream.run()
    except Exception as e:
        logger.error(f"Alpaca stream disconnected or failed: {e}")

def start_stream():
    """
    Daemon loop that keeps the stream alive and reconnects on failure.
    """
    while True:
        try:
            run_stream()
        except Exception as e:
            logger.error(f"Stream error: {e}. Reconnecting in 5 seconds...")
        time.sleep(5)
