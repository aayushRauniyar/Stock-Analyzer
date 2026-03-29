import sqlite3
import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data_snapshots", "mirai.db")

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create all required tables for a fresh start."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Watchlist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                ticker TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Orders (Sync with Alpaca)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                ticker TEXT NOT NULL,
                side TEXT NOT NULL,
                qty INTEGER NOT NULL,
                status TEXT NOT NULL,
                filled_qty INTEGER DEFAULT 0,
                filled_avg_price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Trade Log (Realized P&L / Tax Log)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                qty INTEGER NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                reason TEXT,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 4. Settings (Persistence for Auto-trade, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        conn.commit()

# --- Watchlist Helpers ---

def get_watchlist():
    with get_db() as conn:
        rows = conn.execute("SELECT ticker FROM watchlist ORDER BY ticker ASC").fetchall()
        return [row["ticker"] for row in rows]

def add_to_watchlist(ticker):
    with get_db() as conn:
        conn.execute("INSERT OR IGNORE INTO watchlist (ticker) VALUES (?)", (ticker.upper(),))
        conn.commit()

def remove_from_watchlist(ticker):
    with get_db() as conn:
        conn.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker.upper(),))
        conn.commit()

# --- Order Helpers ---

def log_order(order_id, ticker, side, qty, status="new"):
    with get_db() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO orders (order_id, ticker, side, qty, status, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (order_id, ticker.upper(), side, qty, status, datetime.now().isoformat()))
        conn.commit()

def update_order_status(order_id, status, filled_qty=0, filled_avg_price=None):
    with get_db() as conn:
        conn.execute("""
            UPDATE orders 
            SET status = ?, filled_qty = ?, filled_avg_price = ?, updated_at = ?
            WHERE order_id = ?
        """, (status, filled_qty, filled_avg_price, datetime.now().isoformat(), order_id))
        conn.commit()

def get_orders(limit=50):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM orders ORDER BY updated_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

# --- Trade Log Helpers ---

def add_to_trade_log(ticker, action, qty, price, reason=None):
    total = float(qty) * float(price)
    with get_db() as conn:
        conn.execute("""
            INSERT INTO trade_log (ticker, action, qty, price, total, reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ticker.upper(), action.upper(), qty, price, total, reason))
        conn.commit()

def get_trade_log(limit=100):
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM trade_log ORDER BY date DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]

# --- Settings Helpers ---

def set_setting(key, value):
    with get_db() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()

def get_setting(key, default=None):
    with get_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

if __name__ == "__main__":
    init_db()
    print("✅ Mirai DB initialized.")
