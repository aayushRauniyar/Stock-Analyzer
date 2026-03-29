import json
import logging
import asyncio
import os
import threading
from filelock import FileLock
from alpaca.trading.stream import TradingStream
import time

from backend.config import ALPACA_API_KEY, ALPACA_SECRET_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AlpacaStream")

ORDERS_JSON_PATH = os.path.join(os.path.dirname(__file__), "data_snapshots", "orders.json")
LOCK_PATH = ORDERS_JSON_PATH + ".lock"

def update_orders_json(trade_update):
    """
    Update the orders.json file when a trade execution occurs.
    Locks the file to prevent concurrent write corruption from other modules.
    """
    try:
        lock = FileLock(LOCK_PATH, timeout=5)
        order_data = {}
        with lock:
            orders = []
            if os.path.exists(ORDERS_JSON_PATH):
                try:
                    with open(ORDERS_JSON_PATH, "r") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            orders = data
                        elif "orders" in data:
                            orders = data["orders"]
                except json.JSONDecodeError:
                    orders = []

            # Find and update, or append
            order_id = trade_update.order.id
            updated = False
            
            # Extract basic dictionary summary
            order_data = {
                "id": str(order_id),
                "symbol": trade_update.order.symbol,
                "qty": str(trade_update.order.qty),
                "filled_qty": str(trade_update.order.filled_qty),
                "type": trade_update.order.order_type.value if hasattr(trade_update.order.order_type, 'value') else str(trade_update.order.order_type),
                "side": trade_update.order.side.value if hasattr(trade_update.order.side, 'value') else str(trade_update.order.side),
                "time_in_force": trade_update.order.time_in_force.value if hasattr(trade_update.order.time_in_force, 'value') else str(trade_update.order.time_in_force),
                "limit_price": str(trade_update.order.limit_price) if trade_update.order.limit_price else None,
                "stop_price": str(trade_update.order.stop_price) if trade_update.order.stop_price else None,
                "status": trade_update.order.status.value if hasattr(trade_update.order.status, 'value') else str(trade_update.order.status),
                "created_at": str(trade_update.order.created_at),
                "updated_at": str(trade_update.order.updated_at)
            }

            for i, order in enumerate(orders):
                if order.get("id") == str(order_id):
                    orders[i] = order_data
                    updated = True
                    break
            
            if not updated:
                orders.insert(0, order_data) # Prepend new order

            # Keep only last 50 orders
            orders = orders[:50]

            with open(ORDERS_JSON_PATH, "w") as f:
                json.dump(orders, f, indent=4)
                
            logger.info(f"Updated orders.json with status {order_data['status']} for {order_data['symbol']}")

        # Broadcast SSE via local import to prevent circular dependency
        try:
            from backend.server import broadcast_sse
            broadcast_sse("order_update", order_data)
        except Exception as e:
            logger.error(f"Could not broadcast SSE: {e}")

    except Exception as e:
        logger.error(f"Failed to update orders.json: {e}")

async def trade_update_handler(data):
    """
    Callback fired by Alpaca when an order fills, cancels, etc.
    """
    logger.info(f"Trade update received: {data.event}")
    update_orders_json(data)

def run_stream():
    """
    Blocking call to start the Alpaca TradingStream.
    """
    logger.info("Starting Alpaca Trading Stream...")
    try:
        stream = TradingStream(
            ALPACA_API_KEY,
            ALPACA_SECRET_KEY,
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
