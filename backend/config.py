"""
╔══════════════════════════════════════════════════════════╗
║     MIRAI ARCSPHERE · Risk & Trading Configuration       ║
║     Module 3 — Risk Limits & Position Sizing             ║
╚══════════════════════════════════════════════════════════╝

PURPOSE:
  Centralized configuration for all trading risk limits,
  position sizing parameters, and paper trading settings.
  
PARAMETERS:
  - Daily max loss: 5% of account equity
  - Max position size: 50% of account
  - Stop loss: Dynamic (ATR × 2)
  - Min confidence: 60% (don't trade below this)
  - Min account: $1,000 (paper trading minimum)
"""

import os
from datetime import datetime, time

# ─────────────────────────────────────────────
# ALPACA PAPER TRADING CONFIGURATION
# ─────────────────────────────────────────────

# Paper trading API keys (set via environment variables)
ALPACA_API_KEY = os.getenv("APCA_API_KEY_ID", "YOUR_ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("APCA_API_SECRET_KEY", "YOUR_ALPACA_SECRET_KEY")
ALPACA_BASE_URL = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets/v2")

# ─────────────────────────────────────────────
# RISK MANAGEMENT CONFIGURATION
# ─────────────────────────────────────────────

class RiskLimits:
    """Hard constraints for all trades."""
    
    # Daily maximum loss as % of account equity
    # If realized loss reaches 5%, stop all trading for the day
    DAILY_MAX_LOSS_PCT = 5.0
    
    # Maximum position size as % of account equity
    # No single position can exceed 50% of account
    MAX_POSITION_SIZE_PCT = 50.0
    
    # Minimum account equity to start trading
    # Paper trading minimum (prevents $0 accounts)
    MIN_ACCOUNT_EQUITY = 1_000.0
    
    # Minimum AI signal confidence to place a trade
    # Don't trade unless confidence >= 60%
    MIN_SIGNAL_CONFIDENCE = 60
    
    # Maximum simultaneous positions
    # Prevent over-concentration (up to 5 tickers at once)
    MAX_CONCURRENT_POSITIONS = 5


class PositionSizing:
    """Parameters for calculating position size."""
    
    # Stop loss as ATR multiple
    # Stop = entry - (ATR × ATR_MULTIPLIER)
    ATR_STOP_MULTIPLIER = 2.0
    
    # Risk per trade as % of account
    # Used to calculate qty: qty = (account * risk_pct) / (entry - stop)
    RISK_PER_TRADE_PCT = 1.0
    
    # Minimum position size (qty)
    # Don't trade fewer than 1 share/contract
    MIN_POSITION_QTY = 1
    
    # Maximum single trade size ($ value)
    # Cap to prevent blowups from data errors
    MAX_TRADE_VALUE = 50_000.0


class OrderExecution:
    """Order placement parameters."""
    
    # Order type: "market", "limit", etc.
    ORDER_TYPE = "market"
    
    # Time-in-force: "day", "gtc", "opg", "cls"
    # "day" = cancel at end of market day
    TIME_IN_FORCE = "day"
    
    # Extended hours trading: True/False
    EXTENDED_HOURS = False


class TradingHours:
    """When to trade."""
    
    # Market opens at 9:30 AM ET
    MARKET_OPEN_TIME = time(9, 30)
    
    # Market closes at 4:00 PM ET
    MARKET_CLOSE_TIME = time(16, 0)
    
    # Don't trade in last N minutes of day
    # Prevents slippage from late-day volatility
    NO_TRADE_BEFORE_CLOSE_MINUTES = 15
    
    # Skip trading on these weekdays (0=Monday, 4=Friday)
    # (Currently trades 5 days a week)
    SKIP_TRADING_DAYS = []


# ─────────────────────────────────────────────
# AUTO-TRADING TOGGLE STATE
# ─────────────────────────────────────────────

# File to persist auto-trading toggle state
# Server reads/writes this to remember user preference
AUTO_TRADING_STATE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data_snapshots",
    "auto_trading_enabled.txt"
)

# Default: auto-trading OFF (user must enable via dashboard)
AUTO_TRADING_DEFAULT_ENABLED = False


# ─────────────────────────────────────────────
# LOGGING & PERSISTENCE
# ─────────────────────────────────────────────

# Trade log CSV path (for ATO compliance)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRADE_LOG_PATH = os.path.join(BASE_DIR, "logs", "trade_log.csv")

# Ensure directories exist
os.makedirs(os.path.dirname(TRADE_LOG_PATH), exist_ok=True)

# ─────────────────────────────────────────────
# DISPLAY CONFIGURATION
# ─────────────────────────────────────────────

# Decimal places for price display
PRICE_DECIMAL_PLACES = 2

# Decimal places for percentage display
PERCENT_DECIMAL_PLACES = 2

# Timezone for logging timestamps
TIMEZONE = "Australia/Adelaide"


# ─────────────────────────────────────────────
# VALIDATION HELPERS
# ─────────────────────────────────────────────

def validate_position_size(qty: int, price: float, account_equity: float) -> tuple[bool, str]:
    """
    Validate a proposed position size against limits.
    
    Args:
        qty: Position quantity
        price: Entry price
        account_equity: Current account equity
    
    Returns:
        (is_valid, reason_if_invalid)
    """
    if qty < PositionSizing.MIN_POSITION_QTY:
        return False, f"Qty {qty} < minimum {PositionSizing.MIN_POSITION_QTY}"
    
    position_value = qty * price
    if position_value > PositionSizing.MAX_TRADE_VALUE:
        return False, f"Position value ${position_value:,.0f} > max ${PositionSizing.MAX_TRADE_VALUE:,.0f}"
    
    position_pct = (position_value / account_equity) * 100
    if position_pct > RiskLimits.MAX_POSITION_SIZE_PCT:
        return False, f"Position {position_pct:.1f}% > max {RiskLimits.MAX_POSITION_SIZE_PCT}%"
    
    return True, ""


def get_auto_trading_enabled() -> bool:
    """
    Read the auto-trading toggle state from disk.
    
    Returns:
        True if auto-trading is enabled, False otherwise
    """
    try:
        if os.path.exists(AUTO_TRADING_STATE_FILE):
            with open(AUTO_TRADING_STATE_FILE, "r") as f:
                state = f.read().strip().lower()
                return state == "true" or state == "1"
    except Exception:
        pass
    return AUTO_TRADING_DEFAULT_ENABLED


def set_auto_trading_enabled(enabled: bool) -> None:
    """
    Write the auto-trading toggle state to disk.
    
    Args:
        enabled: True to enable, False to disable
    """
    os.makedirs(os.path.dirname(AUTO_TRADING_STATE_FILE), exist_ok=True)
    with open(AUTO_TRADING_STATE_FILE, "w") as f:
        f.write("true" if enabled else "false")
