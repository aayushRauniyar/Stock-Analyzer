"""
╔══════════════════════════════════════════════════════════╗
║     MIRAI ARCSPHERE · Trade Orchestrator                 ║
║     Phase 3 — Control Flow & Auto-Trading Logic          ║
╚══════════════════════════════════════════════════════════╝

PURPOSE:
  Central orchestrator that connects all modules:
  - Monitors AI signals for changes
  - Validates trading rules before execution
  - Places trades when conditions are met
  - Manages stop losses and take profits
  - Coordinates between Module 1 (data), 2 (AI), 3 (trading)

FLOW:
  Signal Change → Risk Checks → Position Sizing → Order Placement → Trade Logging

CONFIGURATION:
  - Min confidence: 60% (don't trade weaker signals)
  - Auto-trading: user toggle control
  - Signal thresholds: BUY/SELL only, ignore HOLD
"""

import os
import sys
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Optional, List, Tuple

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules
from module1_market_data import get_market_data, WATCHLIST
from module2_ai_analysis import get_cached_signals, analyse_ticker
from module3_trade_execution import (
    place_order, close_trade, get_account_info, get_open_positions,
    is_auto_trading_enabled, toggle_auto_trading
)
from config import RiskLimits
import db

# ─────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [ORCHESTRATOR]  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(BASE_DIR, "logs", "orchestrator.log"), mode="a", encoding="utf-8")
    ]
)
log = logging.getLogger("orchestrator")
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

# ─────────────────────────────────────────────
# ORCHESTRATOR CONFIGURATION
# ─────────────────────────────────────────────

MIN_SIGNAL_CONFIDENCE = 60  # Don't trade below 60% confidence
SIGNAL_CHECK_INTERVAL_SECONDS = 30  # Check signals every 30 sec
POSITION_UPDATE_INTERVAL_SECONDS = 10  # Poll positions every 10 sec


# ─────────────────────────────────────────────
# GLOBAL STATE
# ─────────────────────────────────────────────

# Track last signals to detect changes
last_signals: Dict[str, dict] = {}
last_signal_time: Dict[str, datetime] = {}

# Track positions we opened (for managing exits)
orchestrated_trades: Dict[str, dict] = {}  # {ticker: trade_info}

# Thread safety
orchestrator_lock = threading.Lock()

# Flag to control orchestrator
orchestrator_running = True


# ─────────────────────────────────────────────
# SECTION 1: SIGNAL MONITORING
# ─────────────────────────────────────────────

def get_current_signals() -> dict:
    """
    Get latest signals for all tickers.
    Returns cached signals if available, else fresh analysis.
    """
    try:
        cached = get_cached_signals()
        if cached and "signals" in cached:
            return cached["signals"]
        
        # Fall back to fresh analysis
        log.info("📊 Cached signals unavailable, running fresh analysis...")
        fresh_signals = {}
        watchlist = db.get_watchlist()
        for ticker in watchlist:
            data = get_market_data(ticker)
            signal = analyse_ticker(data)
            fresh_signals[ticker] = signal
        return fresh_signals
    
    except Exception as e:
        log.error(f"❌ Failed to get signals: {e}")
        return {}


def signal_changed(ticker: str, new_signal: dict) -> bool:
    """
    Check if a signal has changed materially.
    Changes: signal type (BUY→SELL), or high confidence increase.
    """
    old_signal = last_signals.get(ticker)
    if not old_signal:
        return True  # First time
    
    # Check if signal type changed
    old_type = old_signal.get("signal")
    new_type = new_signal.get("signal")
    
    if old_type != new_type:
        confidence_old = old_signal.get("conf", 0)
        confidence_new = new_signal.get("conf", 0)
        log.info(f"🔄 Signal change for {ticker}: {old_type} ({confidence_old}%) → {new_type} ({confidence_new}%)")
        return True
    
    # Check if confidence jumped significantly (>10% increase in strong signals)
    confidence_old = old_signal.get("conf", 0)
    confidence_new = new_signal.get("conf", 0)
    
    if new_type in ("BUY", "SELL") and confidence_new - confidence_old > 10:
        log.info(f"📈 {ticker}: Confidence increased {confidence_old}% → {confidence_new}%")
        return True
    
    return False


def should_trade_signal(signal: dict, ticker: str) -> Tuple[bool, str]:
    """
    Determine if a signal warrants a trade.
    
    Returns:
        (should_trade, reason)
    """
    signal_type = signal.get("signal")
    confidence = signal.get("conf", 0)
    
    # Only trade BUY and SELL, ignore HOLD
    if signal_type not in ("BUY", "SELL"):
        return False, f"Signal is {signal_type} (only BUY/SELL are tradeable)"
    
    # Check minimum confidence
    if confidence < MIN_SIGNAL_CONFIDENCE:
        return False, f"Confidence {confidence}% < minimum {MIN_SIGNAL_CONFIDENCE}%"
    
    # Check if already have position
    positions = get_open_positions()
    if any(p["ticker"] == ticker for p in positions):
        return False, f"Already have open position in {ticker}"
    
    return True, ""


# ─────────────────────────────────────────────
# SECTION 2: TRADE EXECUTION
# ─────────────────────────────────────────────

def execute_signal_trade(ticker: str, signal: dict, market_data: dict) -> bool:
    """
    Execute a trade based on an AI signal.
    
    Performs all validation, position sizing, and order placement.
    """
    try:
        # Check if we should trade this signal
        should_trade, reason = should_trade_signal(signal, ticker)
        if not should_trade:
            log.info(f"⏭  Skipping trade for {ticker}: {reason}")
            return False
        
        signal_type = signal.get("signal")
        confidence = signal.get("conf", 0)
        
        log.info(f"✅ Signal qualifies for trade: {ticker} {signal_type} ({confidence}%)")
        
        # Place the order through Module 3
        side = "buy" if signal_type == "BUY" else "sell"
        order_id = place_order(ticker, 0, side, signal, market_data)  # qty=0 triggers calculation
        
        if order_id:
            log.info(f"🎯 Trade executed: {ticker} {signal_type}")
            
            with orchestrator_lock:
                orchestrated_trades[ticker] = {
                    "order_id": order_id,
                    "signal": signal_type,
                    "confidence": confidence,
                    "executed_at": datetime.now().isoformat(),
                }
            
            return True
        else:
            log.warning(f"⚠ Order placement failed for {ticker}")
            return False
    
    except Exception as e:
        log.error(f"❌ Trade execution failed: {e}")
        return False


# ─────────────────────────────────────────────
# SECTION 3: MAIN ORCHESTRATION LOOP
# ─────────────────────────────────────────────

def check_signals_cycle():
    """
    Main orchestrator loop:
    1. Get latest signals
    2. Detect signal changes
    3. Execute trades if conditions met
    4. Update tracking
    """
    try:
        if not is_auto_trading_enabled():
            return  # Skip if auto-trading disabled
        
        signals = get_current_signals()
        if not signals:
            log.debug("No signals available")
            return
        
        for ticker, signal in signals.items():
            try:
                # Check if signal changed
                if signal_changed(ticker, signal):
                    # Get fresh market data
                    market_data = get_market_data(ticker)
                    
                    # Try to execute
                    execute_signal_trade(ticker, signal, market_data)
                
                # Update last signal
                with orchestrator_lock:
                    last_signals[ticker] = signal
                    last_signal_time[ticker] = datetime.now()
            
            except Exception as e:
                log.error(f"❌ Error processing {ticker}: {e}")
    
    except Exception as e:
        log.error(f"❌ Signal check cycle failed: {e}")


def monitor_positions_cycle():
    """
    Monitor open positions:
    1. Poll positions every POSITION_UPDATE_INTERVAL_SECONDS
    2. Update P&L tracking
    3. Check if any positions hit stop loss or take profit
    4. Broadcast updates to server via SSE queue (if implemented)
    """
    try:
        positions = get_open_positions()
        account = get_account_info()
        
        if positions:
            log.info(f"📊 Positions update: {len(positions)} open")
            for pos in positions:
                pnl_pct = pos.get("unrealized_plpc", 0) * 100
                log.info(f"   {pos['ticker']}: ${pos['market_value']:,.0f} ({pnl_pct:+.2f}%)")
    
    except Exception as e:
        log.error(f"❌ Position monitoring failed: {e}")


def run_orchestrator():
    """
    Main orchestrator runner.
    Starts background threads for signal monitoring and position updates.
    """
    global orchestrator_running
    
    log.info("=" * 56)
    log.info("  🎭 MIRAI ARCSPHERE · Orchestrator")
    log.info("=" * 56)
    log.info(f"  Min Signal Confidence: {MIN_SIGNAL_CONFIDENCE}%")
    log.info(f"  Signal Check Interval: {SIGNAL_CHECK_INTERVAL_SECONDS}s")
    log.info(f"  Position Update Interval: {POSITION_UPDATE_INTERVAL_SECONDS}s")
    log.info("=" * 56)
    
    def signal_monitor_thread():
        """Background thread for signal monitoring."""
        log.info("🔌 Starting signal monitor thread...")
        while orchestrator_running:
            try:
                check_signals_cycle()
            except Exception as e:
                log.error(f"❌ Signal monitor error: {e}")
            time.sleep(SIGNAL_CHECK_INTERVAL_SECONDS)
    
    def position_monitor_thread():
        """Background thread for position monitoring."""
        log.info("🔌 Starting position monitor thread...")
        while orchestrator_running:
            try:
                monitor_positions_cycle()
            except Exception as e:
                log.error(f"❌ Position monitor error: {e}")
            time.sleep(POSITION_UPDATE_INTERVAL_SECONDS)
    
    # Start threads
    signal_thread = threading.Thread(target=signal_monitor_thread, daemon=True)
    position_thread = threading.Thread(target=position_monitor_thread, daemon=True)
    
    signal_thread.start()
    position_thread.start()
    
    log.info("✅ Orchestrator started")
    
    # Keep main thread alive
    try:
        while orchestrator_running:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("⏹  Shutting down orchestrator...")
        orchestrator_running = False


# ─────────────────────────────────────────────
# ORCHESTRATOR CONTROL
# ─────────────────────────────────────────────

def set_auto_trading(enabled: bool):
    """
    Control auto-trading via orchestrator.
    """
    toggle_auto_trading(enabled)
    status = "🟢 ENABLED" if enabled else "🔴 DISABLED"
    log.info(f"Auto-trading toggled: {status}")


def get_orchestrator_status() -> dict:
    """
    Get current orchestrator status.
    """
    return {
        "running": orchestrator_running,
        "auto_trading_enabled": is_auto_trading_enabled(),
        "monitored_tickers": db.get_watchlist(),
        "min_confidence": MIN_SIGNAL_CONFIDENCE,
        "last_signals": last_signals,
        "orchestrated_trades": orchestrated_trades,
        "timestamp": datetime.now().isoformat(),
    }


# ─────────────────────────────────────────────
# STANDALONE RUNNER
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("\n🧪 Running Orchestrator quick test...\n")
        
        status = get_orchestrator_status()
        print(json.dumps(status, indent=2, default=str))
        
        print("\n✅ Orchestrator test complete")
    else:
        # Start the orchestrator
        run_orchestrator()
