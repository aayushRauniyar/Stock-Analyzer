"""
╔══════════════════════════════════════════════════════════╗
║     MIRAI ARCSPHERE · 未来アークスフィア                   ║
║     Module 3 — Trade Execution Engine (Hands)            ║
║     Version: 1.0.0                                       ║
║     Status:  ✅ Active (Paper Trading)                   ║
╚══════════════════════════════════════════════════════════╝

PURPOSE:
  The hands of Mirai ArcSphere. Executes trades on Alpaca
  paper trading account with strict risk management, position
  sizing, and ATO-compliant tax logging.

FEATURES:
  ✅ Alpaca paper trading integration
  ✅ ATR-based dynamic stop loss
  ✅ Risk-based position sizing
  ✅ Daily loss limit (5%) enforcement
  ✅ Max position size (50%) enforcement
  ✅ Automatic trade logging for ATO compliance
  ✅ Position tracking and P&L calculation

DEPENDENCIES:
  pip install alpaca-trade-api pandas pytz
"""

import os
import sys
import json
import logging
import csv
import threading
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict
import pandas as pd
import pytz

# Add backend directory to path for module imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    RiskLimits, PositionSizing, OrderExecution, TradingHours,
    ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL,
    TRADE_LOG_PATH, TIMEZONE, validate_position_size,
    get_auto_trading_enabled, set_auto_trading_enabled
)
from models import TradeRecord

# ─────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [MODULE-3]  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(BASE_DIR, "logs", "module3.log"), mode="a", encoding="utf-8")
    ]
)
log = logging.getLogger("module3")
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

# ─────────────────────────────────────────────
# ALPACA API CLIENT
# ─────────────────────────────────────────────

api = None

def init_alpaca_api():
    """Initialize Alpaca API client."""
    global api
    try:
        import alpaca_trade_api as tradeapi
        api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)
        log.info("✅ Alpaca API initialized (paper trading)")
        return api
    except Exception as e:
        log.error(f"❌ Failed to initialize Alpaca API: {e}")
        return None


# ─────────────────────────────────────────────
# GLOBAL STATE: TRADE TRACKING
# ─────────────────────────────────────────────

# All trades (open and closed)
all_trades: Dict[str, TradeRecord] = {}
trades_lock = threading.Lock()

# Daily loss tracking
daily_loss_start = datetime.now().date()
daily_realized_loss = 0.0


# ─────────────────────────────────────────────
# SECTION 1: ACCOUNT & RISK CHECKS
# ─────────────────────────────────────────────

def get_account_info() -> dict:
    """
    Get current account status from Alpaca.
    
    Returns:
        Dict with equity, cash, positions, etc.
    """
    global api
    if api is None:
        api = init_alpaca_api()
    
    try:
        account = api.get_account()
        return {
            "equity": float(account.equity),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "portfolio_value": float(account.portfolio_value),
            "unrealized_pl": float(account.unrealized_pl),
            "unrealized_plpc": float(account.unrealized_plpc) if account.unrealized_plpc else 0,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        log.error(f"❌ Failed to get account info: {e}")
        return {}


def get_open_positions() -> List[dict]:
    """Get all currently open positions from Alpaca."""
    global api
    if api is None: api = init_alpaca_api()
    try:
        positions = api.list_positions()
        result = []
        for pos in positions:
            result.append({
                "ticker": pos.symbol,
                "qty": int(pos.qty),
                "entry_price": float(pos.avg_fill_price),
                "current_price": float(pos.current_price),
                "market_value": float(pos.market_value),
                "unrealized_pl": float(pos.unrealized_pl),
                "unrealized_plpc": float(pos.unrealized_plpc) if pos.unrealized_plpc else 0,
                "side": pos.side,
            })
        return result
    except Exception as e:
        log.error(f"❌ Failed to list positions: {e}")
        return []


def get_orders(limit: int = 50) -> List[dict]:
    """Get recent orders from Alpaca."""
    global api
    if api is None: api = init_alpaca_api()
    try:
        orders = api.list_orders(status="all", limit=limit, nested=True)
        result = []
        for o in orders:
            result.append({
                "id": o.id,
                "ticker": o.symbol,
                "qty": int(o.qty),
                "filled_qty": int(o.filled_qty),
                "side": o.side.upper(),
                "type": o.type,
                "status": o.status.upper(),
                "created_at": o.created_at.isoformat() if hasattr(o.created_at, 'isoformat') else str(o.created_at),
                "filled_at": o.filled_at.isoformat() if o.filled_at and hasattr(o.filled_at, 'isoformat') else str(o.filled_at),
                "limit_price": float(o.limit_price) if o.limit_price else None,
                "filled_avg_price": float(o.filled_avg_price) if o.filled_avg_price else None,
            })
        return result
    except Exception as e:
        log.error(f"❌ Failed to list orders: {e}")
        return []



def get_daily_loss() -> float:
    """
    Calculate today's realized loss so far.
    
    Returns:
        Total realized loss for today (positive number)
    """
    global daily_loss_start, daily_realized_loss
    
    # Reset if new day
    if datetime.now().date() != daily_loss_start:
        daily_loss_start = datetime.now().date()
        daily_realized_loss = 0.0
    
    return daily_realized_loss


def check_daily_loss_limit() -> Tuple[bool, str]:
    """
    Check if daily loss limit has been exceeded.
    
    Returns:
        (can_trade, reason_if_blocked)
    """
    account = get_account_info()
    if not account:
        return False, "Could not retrieve account info"
    
    equity = account.get("equity", 0)
    daily_loss = get_daily_loss()
    daily_loss_pct = (daily_loss / equity * 100) if equity > 0 else 0
    
    if daily_loss_pct >= RiskLimits.DAILY_MAX_LOSS_PCT:
        reason = f"Daily loss limit reached: {daily_loss_pct:.2f}% >= {RiskLimits.DAILY_MAX_LOSS_PCT}%"
        log.warning(f"⚠ {reason}")
        return False, reason
    
    return True, ""


def check_position_limits(ticker: str) -> Tuple[bool, str]:
    """
    Check if opening a new position would violate limits.
    
    Returns:
        (can_trade, reason_if_blocked)
    """
    positions = get_open_positions()
    
    # Check: max concurrent positions
    if len(positions) >= RiskLimits.MAX_CONCURRENT_POSITIONS:
        reason = f"Max concurrent positions reached ({len(positions)})"
        log.warning(f"⚠ {reason}")
        return False, reason
    
    # Check: already have position in this ticker
    for pos in positions:
        if pos["ticker"] == ticker:
            reason = f"Already have open position in {ticker}"
            log.warning(f"⚠ {reason}")
            return False, reason
    
    return True, ""


# ─────────────────────────────────────────────
# SECTION 2: POSITION SIZING
# ─────────────────────────────────────────────

def calculate_position_size(
    ticker: str,
    entry_price: float,
    stop_loss_price: float,
    atr: float,
    account_equity: float
) -> Tuple[int, float, float]:
    """
    Calculate position size using risk-based sizing.
    
    Formula:
      risk_dollars = account_equity * RISK_PER_TRADE_PCT / 100
      position_qty = risk_dollars / (entry_price - stop_price)
    
    Args:
        ticker: Symbol
        entry_price: Entry price
        stop_loss_price: Stop loss price
        atr: Average true range for volatility
        account_equity: Current account equity
    
    Returns:
        (qty, max_loss_dollars, take_profit_price)
    """
    # Calculate risk in dollars
    risk_dollars = (account_equity * PositionSizing.RISK_PER_TRADE_PCT) / 100
    
    # Calculate position size
    price_risk = abs(entry_price - stop_loss_price)
    if price_risk <= 0:
        log.warning(f"⚠ Invalid stop loss distance for {ticker}")
        return 0, 0, 0
    
    qty = int(risk_dollars / price_risk)
    qty = max(qty, PositionSizing.MIN_POSITION_QTY)
    
    # Validate position
    is_valid, reason = validate_position_size(qty, entry_price, account_equity)
    if not is_valid:
        log.warning(f"⚠ Position sizing validation failed: {reason}")
        qty = 0
    
    # Calculate take profit: entry + (entry - stop) * 2 (2:1 reward:risk)
    risk_distance = entry_price - stop_loss_price
    take_profit = entry_price + (risk_distance * 2)
    
    max_loss = qty * price_risk
    
    log.info(f"📊 Position sizing for {ticker}:")
    log.info(f"   Entry: ${entry_price:.2f} | Stop: ${stop_loss_price:.2f} | TP: ${take_profit:.2f}")
    log.info(f"   Qty: {qty} | Max Loss: ${max_loss:.2f} | Risk: {PositionSizing.RISK_PER_TRADE_PCT}%")
    
    return qty, max_loss, take_profit


def calculate_stop_loss(current_price: float, atr: float, side: str = "BUY") -> float:
    """
    Calculate ATR-based stop loss.
    
    Stop = entry ± (ATR × ATR_MULTIPLIER)
    
    Args:
        current_price: Entry price
        atr: Average true range
        side: "BUY" (stop below) or "SELL" (stop above)
    
    Returns:
        Stop loss price
    """
    stop_distance = atr * PositionSizing.ATR_STOP_MULTIPLIER
    
    if side == "BUY":
        stop = current_price - stop_distance
    else:  # SELL
        stop = current_price + stop_distance
    
    return max(stop, 0.01)  # Prevent negative prices


# ─────────────────────────────────────────────
# SECTION 3: ORDER EXECUTION
# ─────────────────────────────────────────────

def place_order(
    ticker: str,
    qty: int,
    side: str,
    signal: dict,
    market_data: dict
) -> Optional[str]:
    """
    Place an order on Alpaca paper trading.
    
    Args:
        ticker: Symbol
        qty: Quantity
        side: "buy" or "sell"
        signal: AI signal dict (for logging)
        market_data: Market data (for stop loss calc)
    
    Returns:
        Order ID if successful, None otherwise
    """
    global api
    if api is None:
        api = init_alpaca_api()
    
    try:
        # Check daily loss limit
        can_trade, reason = check_daily_loss_limit()
        if not can_trade:
            log.warning(f"❌ Trade blocked: {reason}")
            return None
        
        # Check position limits
        can_trade, reason = check_position_limits(ticker)
        if not can_trade:
            log.warning(f"❌ Trade blocked: {reason}")
            return None
        
        # Calculate position sizing
        atr = market_data.get("atr_14", 1.0)
        entry_price = market_data.get("price", 0)
        account = get_account_info()
        equity = account.get("equity", 0)
        
        stop_loss = calculate_stop_loss(entry_price, atr, side="BUY" if side.lower() == "buy" else "SELL")
        qty_calc, max_loss, take_profit = calculate_position_size(
            ticker, entry_price, stop_loss, atr, equity
        )
        
        if qty_calc <= 0:
            log.warning(f"❌ Position sizing resulted in 0 qty")
            return None
        
        # Place market order
        log.info(f"🚀 Placing {side.upper()} order: {qty_calc} {ticker} @ market")
        
        order = api.submit_order(
            symbol=ticker,
            qty=qty_calc,
            side=side.lower(),
            type=OrderExecution.ORDER_TYPE,
            time_in_force=OrderExecution.TIME_IN_FORCE,
        )
        
        log.info(f"✅ Order placed: {order.id} ({order.status})")
        
        # Record trade
        trade = TradeRecord(
            trade_id=f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            ticker=ticker,
            entry_date=datetime.now(),
            entry_price=entry_price,
            entry_qty=qty_calc,
            entry_side=side.upper(),
            entry_order_id=order.id,
            exit_date=None,
            exit_price=None,
            exit_qty=None,
            exit_side=None,
            exit_reason=None,
            exit_order_id=None,
            signal_type=signal.get("signal", "UNKNOWN"),
            signal_confidence=signal.get("conf", 0),
            signal_reasoning=signal.get("reason", ""),
            analysis_timestamp=datetime.now(),
            stop_loss_price=stop_loss,
            take_profit_price=take_profit,
            risk_per_trade_pct=PositionSizing.RISK_PER_TRADE_PCT,
            max_loss_on_trade=max_loss,
            gross_p_l=None,
            net_p_l=None,
            p_l_pct=None,
            hold_period_days=None,
            is_short_term=None,
            capital_gains_type="CGT",
            notes=f"Signal confidence: {signal.get('conf', 0)}%"
        )
        
        with trades_lock:
            all_trades[order.id] = trade
        
        return order.id
        
    except Exception as e:
        log.error(f"❌ Order placement failed: {e}")
        return None


def direct_place_order(ticker: str, qty: int, side: str, order_type: str = "market") -> Optional[str]:
    """
    Simplified order placement (bypasses signal-based ATR sizing).
    Returns order ID.
    """
    global api
    if api is None: api = init_alpaca_api()
    try:
        log.info(f"🚀 Direct order: {side.upper()} {qty} {ticker} @ {order_type}")
        order = api.submit_order(
            symbol=ticker,
            qty=qty,
            side=side.lower(),
            type=order_type,
            time_in_force="day"
        )
        return order.id
    except Exception as e:
        log.error(f"❌ Direct order failed: {e}")
        return None



# ─────────────────────────────────────────────
# SECTION 4: TRADE LOGGING (ATO COMPLIANCE)
# ─────────────────────────────────────────────

def write_trade_log(trade: TradeRecord) -> None:
    """
    Write a completed trade to the tax log CSV.
    
    Format is ATO-compliant for Australian capital gains tax.
    """
    try:
        os.makedirs(os.path.dirname(TRADE_LOG_PATH), exist_ok=True)
        
        file_exists = os.path.exists(TRADE_LOG_PATH)
        csv_row = trade.to_csv_row()
        
        with open(TRADE_LOG_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_row.keys())
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(csv_row)
        
        log.info(f"💾 Trade logged to {TRADE_LOG_PATH}: {trade.ticker} {trade.entry_side}")
        
    except Exception as e:
        log.error(f"❌ Failed to write trade log: {e}")


def get_trade_log() -> List[dict]:
    """
    Read the trade log CSV and return as list of dicts.
    
    Returns:
        List of trade records
    """
    try:
        if not os.path.exists(TRADE_LOG_PATH):
            return []
        
        df = pd.read_csv(TRADE_LOG_PATH)
        return df.to_dict("records")
        
    except Exception as e:
        log.error(f"❌ Failed to read trade log: {e}")
        return []


# ─────────────────────────────────────────────
# SECTION 5: TRADE MANAGEMENT
# ─────────────────────────────────────────────

def close_trade(trade_id: str, exit_reason: str = "manual") -> bool:
    """
    Close an open trade and record exit.
    
    Args:
        trade_id: Trade ID to close
        exit_reason: Why it's being closed
    
    Returns:
        True if closed successfully
    """
    global api, daily_realized_loss
    if api is None:
        api = init_alpaca_api()
    
    try:
        with trades_lock:
            if trade_id not in all_trades:
                log.warning(f"⚠ Trade {trade_id} not found")
                return False
            
            trade = all_trades[trade_id]
        
        # Close position on Alpaca
        positions = get_open_positions()
        pos = next((p for p in positions if p["ticker"] == trade.ticker), None)
        
        if not pos:
            log.warning(f"⚠ No open position for {trade.ticker}")
            return False
        
        # Close the position
        log.info(f"🔒 Closing position: {trade.ticker} {pos['qty']} shares")
        
        order = api.submit_order(
            symbol=trade.ticker,
            qty=pos["qty"],
            side="sell" if pos["side"] == "long" else "buy",
            type="market",
            time_in_force="day",
        )
        
        # Update trade record
        with trades_lock:
            trade.mark_closed(
                exit_price=pos["current_price"],
                exit_qty=pos["qty"],
                exit_reason=exit_reason,
                exit_order_id=order.id
            )
            
            # Track daily realized loss
            if trade.net_p_l and trade.net_p_l < 0:
                daily_realized_loss += abs(trade.net_p_l)
        
        # Log the trade
        write_trade_log(trade)
        log.info(f"✅ Trade closed: P&L ${trade.net_p_l:.2f} ({trade.p_l_pct:.2f}%)")
        
        return True
        
    except Exception as e:
        log.error(f"❌ Failed to close trade: {e}")
        return False


# ─────────────────────────────────────────────
# SECTION 6: AUTO-TRADING TOGGLE
# ─────────────────────────────────────────────

def toggle_auto_trading(enabled: bool) -> None:
    """
    Enable or disable auto-trading.
    Persists state to disk for dashboard to read.
    """
    set_auto_trading_enabled(enabled)
    status = "🟢 ENABLED" if enabled else "🔴 DISABLED"
    log.info(f"Auto-trading {status}")


def is_auto_trading_enabled() -> bool:
    """Check if auto-trading is currently enabled."""
    return get_auto_trading_enabled()


# ─────────────────────────────────────────────
# STANDALONE TESTER
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("\n🧪 Running Module 3 quick test...\n")
        
        init_alpaca_api()
        
        # Get account info
        account = get_account_info()
        print(f"💰 Account:")
        for k, v in account.items():
            if isinstance(v, float):
                print(f"   {k}: ${v:,.2f}")
            else:
                print(f"   {k}: {v}")
        
        # Get positions
        positions = get_open_positions()
        print(f"\n📊 Open Positions: {len(positions)}")
        for pos in positions:
            print(f"   {pos['ticker']}: {pos['qty']} shares @ ${pos['entry_price']:.2f}")
        
        # Check risk limits
        can_trade, reason = check_daily_loss_limit()
        print(f"\n✅ Daily loss check: {can_trade}")
        if not can_trade:
            print(f"   Reason: {reason}")
        
        print("\n✅ Module 3 test complete")
    else:
        print("Usage: python module3_trade_execution.py test")
