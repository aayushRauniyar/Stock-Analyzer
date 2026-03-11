"""
╔══════════════════════════════════════════════════════════╗
║     MIRAI ARCSPHERE · 未来アークスフィア                   ║
║     Module 1 — Market Data Engine                        ║
║     Version: 1.0.0                                       ║
║     Status:  ✅ Active                                   ║
╚══════════════════════════════════════════════════════════╝

PURPOSE:
  The eyes of Mirai ArcSphere. Fetches real-time and
  historical ETF price data, calculates technical indicators,
  detects market hours, and schedules automatic data cycles.

WHAT THIS MODULE PROVIDES TO OTHER MODULES:
  - get_market_data(ticker)     → price + indicators dict
  - get_all_etf_data()          → data for all watched ETFs
  - is_market_open()            → True/False (market hours check)
  - get_market_schedule()       → next open/close times (Adelaide AEST)
  - run_data_scheduler()        → starts the automatic cycle loop

DEPENDENCIES:
  pip install yfinance ta pandas numpy alpaca-trade-api schedule pytz
"""

import os
import json
import time
import logging
import schedule
import pytz
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from ta.momentum  import RSIIndicator, StochasticOscillator
from ta.trend     import MACD, SMAIndicator, EMAIndicator, ADXIndicator
from ta.volatility import BollingerBands, AverageTrueRange

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

# ETFs to watch — easily add more here
WATCHLIST = ["SPY", "QQQ", "VTI"]

# How often to fetch data during market hours (minutes)
FETCH_INTERVAL_MINUTES = 60

# How many days of history to load for indicator calculations
HISTORY_DAYS = 90

# Timezone for Adelaide, Australia
ADELAIDE_TZ = pytz.timezone("Australia/Adelaide")
MARKET_TZ   = pytz.timezone("America/New_York")

# Alpaca API (used for precise market open/close check)
# Set these as environment variables or paste directly
ALPACA_API_KEY    = os.getenv("ALPACA_API_KEY",    "YOUR_ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "YOUR_ALPACA_SECRET_KEY")
ALPACA_BASE_URL   = "https://paper-api.alpaca.markets"

# Output folder for data snapshots (used by Module 4 dashboard)
OUTPUT_DIR = "data_snapshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# LOGGING SETUP
# ─────────────────────────────────────────────
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [MODULE-1]  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/module1.log", mode="a", encoding="utf-8")
    ]
)
log = logging.getLogger("module1")
os.makedirs("logs", exist_ok=True)


# ─────────────────────────────────────────────
# SECTION 1: MARKET HOURS
# ─────────────────────────────────────────────

def is_market_open() -> bool:
    """
    Check if the US market is currently open.
    Uses Alpaca API for precision — falls back to time-based check.

    Returns:
        True if market is open, False otherwise
    """
    try:
        import alpaca_trade_api as tradeapi
        api   = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)
        clock = api.get_clock()
        is_open = clock.is_open
        log.info(f"Market status (Alpaca): {'🟢 OPEN' if is_open else '🔴 CLOSED'}")
        return is_open
    except Exception:
        # Fallback: manual time check
        now_ny = datetime.now(MARKET_TZ)
        weekday = now_ny.weekday()  # 0=Monday, 6=Sunday
        hour    = now_ny.hour
        minute  = now_ny.minute
        is_open = (
            weekday < 5 and                          # Mon–Fri
            (hour > 9 or (hour == 9 and minute >= 30)) and  # After 9:30 AM
            hour < 16                                # Before 4:00 PM
        )
        log.info(f"Market status (fallback time check): {'🟢 OPEN' if is_open else '🔴 CLOSED'}")
        return is_open


def get_market_schedule() -> dict:
    """
    Get the next market open and close times, converted to Adelaide time.

    Returns:
        Dict with next_open, next_close, and current Adelaide time
    """
    now_adelaide = datetime.now(ADELAIDE_TZ)

    try:
        import alpaca_trade_api as tradeapi
        api   = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)
        clock = api.get_clock()

        next_open  = clock.next_open.astimezone(ADELAIDE_TZ)
        next_close = clock.next_close.astimezone(ADELAIDE_TZ)

        return {
            "is_open":          clock.is_open,
            "current_adelaide": now_adelaide.strftime("%Y-%m-%d %H:%M %Z"),
            "next_open_aest":   next_open.strftime("%Y-%m-%d %H:%M %Z"),
            "next_close_aest":  next_close.strftime("%Y-%m-%d %H:%M %Z"),
            "next_open_ny":     clock.next_open.strftime("%Y-%m-%d %H:%M ET"),
            "next_close_ny":    clock.next_close.strftime("%Y-%m-%d %H:%M ET"),
        }
    except Exception as e:
        log.warning(f"Could not fetch market schedule from Alpaca: {e}")
        return {
            "is_open":          is_market_open(),
            "current_adelaide": now_adelaide.strftime("%Y-%m-%d %H:%M %Z"),
            "note":             "Schedule unavailable — check Alpaca API key",
        }


# ─────────────────────────────────────────────
# SECTION 2: DATA FETCHING
# ─────────────────────────────────────────────

def fetch_raw_data(ticker: str, days: int = HISTORY_DAYS) -> pd.DataFrame:
    """
    Fetch raw OHLCV (Open, High, Low, Close, Volume) data from Yahoo Finance.

    Args:
        ticker: ETF symbol e.g. "SPY"
        days:   Number of calendar days of history

    Returns:
        DataFrame with OHLCV columns, or empty DataFrame on failure
    """
    try:
        log.info(f"📥 Fetching {days}d history for {ticker}...")
        period = f"{days}d"
        df = yf.Ticker(ticker).history(period=period, interval="1d")

        if df.empty:
            log.warning(f"⚠ No data returned for {ticker}")
            return pd.DataFrame()

        # Clean up — drop timezone from index for easier handling
        df.index = df.index.tz_localize(None)
        log.info(f"✅ {ticker}: {len(df)} rows fetched ({df.index[0].date()} → {df.index[-1].date()})")
        return df

    except Exception as e:
        log.error(f"❌ Failed to fetch {ticker}: {e}")
        return pd.DataFrame()


# ─────────────────────────────────────────────
# SECTION 3: TECHNICAL INDICATORS
# ─────────────────────────────────────────────

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all technical indicators on a price DataFrame.

    Indicators calculated:
      Momentum:   RSI-14, Stochastic %K/%D
      Trend:      MACD, MACD Signal, SMA-20, SMA-50, EMA-20, ADX
      Volatility: Bollinger Bands (upper/mid/lower), ATR-14
      Volume:     Volume SMA-20, Volume ratio vs average

    Args:
        df: DataFrame with at least Close, High, Low, Volume columns

    Returns:
        DataFrame with all indicator columns added
    """
    if df.empty or len(df) < 20:
        log.warning("Not enough data to calculate indicators (need 20+ rows)")
        return df

    close  = df["Close"]
    high   = df["High"]
    low    = df["Low"]
    volume = df["Volume"]

    # ── Momentum ──────────────────────────────
    df["RSI_14"]     = RSIIndicator(close, window=14).rsi()

    stoch            = StochasticOscillator(high, low, close, window=14, smooth_window=3)
    df["STOCH_K"]    = stoch.stoch()
    df["STOCH_D"]    = stoch.stoch_signal()

    # ── Trend ──────────────────────────────────
    macd             = MACD(close, window_slow=26, window_fast=12, window_sign=9)
    df["MACD"]       = macd.macd()
    df["MACD_SIGNAL"]= macd.macd_signal()
    df["MACD_HIST"]  = macd.macd_diff()     # Histogram (MACD - Signal)

    df["SMA_20"]     = SMAIndicator(close, window=20).sma_indicator()
    df["SMA_50"]     = SMAIndicator(close, window=50).sma_indicator()
    df["EMA_20"]     = EMAIndicator(close, window=20).ema_indicator()

    df["ADX"]        = ADXIndicator(high, low, close, window=14).adx()

    # ── Volatility ─────────────────────────────
    bb               = BollingerBands(close, window=20, window_dev=2)
    df["BB_UPPER"]   = bb.bollinger_hband()
    df["BB_MID"]     = bb.bollinger_mavg()
    df["BB_LOWER"]   = bb.bollinger_lband()
    df["BB_WIDTH"]   = bb.bollinger_wband()   # Band width (volatility measure)
    df["BB_PCT"]     = bb.bollinger_pband()   # % position within bands (0–1)

    df["ATR_14"]     = AverageTrueRange(high, low, close, window=14).average_true_range()

    # ── Volume ────────────────────────────────
    df["VOL_SMA_20"] = SMAIndicator(volume.astype(float), window=20).sma_indicator()
    df["VOL_RATIO"]  = volume / df["VOL_SMA_20"]  # > 1 = above average volume

    log.info(f"📊 Indicators calculated: {len([c for c in df.columns if c not in ['Open','High','Low','Close','Volume','Dividends','Stock Splits']])} indicators added")
    return df


# ─────────────────────────────────────────────
# SECTION 4: SIGNAL SUMMARY
# ─────────────────────────────────────────────

def generate_signal_summary(df: pd.DataFrame, ticker: str) -> dict:
    """
    Generate a clean, structured data package from the latest row.
    This is what gets passed to Module 2 (AI Analysis Engine).

    Args:
        df:     DataFrame with indicators already calculated
        ticker: ETF symbol

    Returns:
        Dict with all current values, signals, and context
    """
    if df.empty:
        return {"ticker": ticker, "error": "No data available"}

    latest = df.iloc[-1]
    prev   = df.iloc[-2] if len(df) > 1 else latest

    # ── Price context ──────────────────────────
    price        = float(latest["Close"])
    prev_price   = float(prev["Close"])
    daily_change = ((price - prev_price) / prev_price) * 100

    # ── Trend signals ──────────────────────────
    sma20        = float(latest["SMA_20"]) if not pd.isna(latest["SMA_20"]) else None
    sma50        = float(latest["SMA_50"]) if not pd.isna(latest["SMA_50"]) else None
    above_sma20  = price > sma20 if sma20 else None
    above_sma50  = price > sma50 if sma50 else None
    golden_cross = (sma20 > sma50) if (sma20 and sma50) else None  # Bullish when True

    # ── Bollinger Band position ────────────────
    bb_pct = float(latest["BB_PCT"]) if not pd.isna(latest["BB_PCT"]) else None
    if bb_pct is not None:
        if bb_pct > 0.8:   bb_signal = "OVERBOUGHT"
        elif bb_pct < 0.2: bb_signal = "OVERSOLD"
        else:              bb_signal = "NEUTRAL"
    else:
        bb_signal = "UNKNOWN"

    # ── MACD signal ────────────────────────────
    macd     = float(latest["MACD"])      if not pd.isna(latest["MACD"])      else None
    macd_sig = float(latest["MACD_SIGNAL"]) if not pd.isna(latest["MACD_SIGNAL"]) else None
    macd_hist= float(latest["MACD_HIST"]) if not pd.isna(latest["MACD_HIST"]) else None
    if macd and macd_sig:
        macd_signal = "BULLISH" if macd > macd_sig else "BEARISH"
    else:
        macd_signal = "UNKNOWN"

    # ── RSI signal ─────────────────────────────
    rsi = float(latest["RSI_14"]) if not pd.isna(latest["RSI_14"]) else None
    if rsi:
        if rsi > 70:   rsi_signal = "OVERBOUGHT"
        elif rsi < 30: rsi_signal = "OVERSOLD"
        else:          rsi_signal = "NEUTRAL"
    else:
        rsi_signal = "UNKNOWN"

    # ── Recent price history (last 5 days) ─────
    recent = df.tail(5)[["Close", "RSI_14", "MACD", "SMA_20", "SMA_50", "VOL_RATIO"]].copy()
    recent.index = recent.index.strftime("%Y-%m-%d")
    recent_str = recent.round(2).to_string()

    # ── Package everything ─────────────────────
    return {
        "ticker":           ticker,
        "timestamp":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "price":            round(price, 2),
        "prev_close":       round(prev_price, 2),
        "daily_change_pct": round(daily_change, 3),

        # Trend
        "sma_20":           round(sma20, 2)     if sma20    else None,
        "sma_50":           round(sma50, 2)     if sma50    else None,
        "ema_20":           round(float(latest["EMA_20"]), 2) if not pd.isna(latest["EMA_20"]) else None,
        "above_sma20":      above_sma20,
        "above_sma50":      above_sma50,
        "golden_cross":     golden_cross,
        "adx":              round(float(latest["ADX"]), 2) if not pd.isna(latest["ADX"]) else None,

        # Momentum
        "rsi":              round(rsi, 2)       if rsi      else None,
        "rsi_signal":       rsi_signal,
        "stoch_k":          round(float(latest["STOCH_K"]), 2) if not pd.isna(latest["STOCH_K"]) else None,
        "stoch_d":          round(float(latest["STOCH_D"]), 2) if not pd.isna(latest["STOCH_D"]) else None,

        # MACD
        "macd":             round(macd, 4)      if macd     else None,
        "macd_signal_line": round(macd_sig, 4)  if macd_sig else None,
        "macd_histogram":   round(macd_hist, 4) if macd_hist else None,
        "macd_signal":      macd_signal,

        # Bollinger Bands
        "bb_upper":         round(float(latest["BB_UPPER"]), 2) if not pd.isna(latest["BB_UPPER"]) else None,
        "bb_mid":           round(float(latest["BB_MID"]), 2)   if not pd.isna(latest["BB_MID"])   else None,
        "bb_lower":         round(float(latest["BB_LOWER"]), 2) if not pd.isna(latest["BB_LOWER"]) else None,
        "bb_pct":           round(bb_pct, 3)    if bb_pct   else None,
        "bb_signal":        bb_signal,
        "atr_14":           round(float(latest["ATR_14"]), 3)   if not pd.isna(latest["ATR_14"])   else None,

        # Volume
        "volume":           int(latest["Volume"]),
        "vol_sma_20":       int(latest["VOL_SMA_20"]) if not pd.isna(latest["VOL_SMA_20"]) else None,
        "vol_ratio":        round(float(latest["VOL_RATIO"]), 2) if not pd.isna(latest["VOL_RATIO"]) else None,

        # Recent data string (for AI prompt in Module 2)
        "recent_5d":        recent_str,
    }


# ─────────────────────────────────────────────
# SECTION 5: MAIN DATA PIPELINE
# ─────────────────────────────────────────────

def get_market_data(ticker: str) -> dict:
    """
    Full pipeline for one ETF: fetch → indicators → summary.
    This is the PRIMARY function called by other modules.

    Args:
        ticker: ETF symbol e.g. "SPY"

    Returns:
        Clean data dict ready for Module 2 (AI Analysis)
    """
    log.info(f"🔄 Running data pipeline for {ticker}")
    df = fetch_raw_data(ticker)
    if df.empty:
        return {"ticker": ticker, "error": "Data fetch failed"}
    df = calculate_indicators(df)
    summary = generate_signal_summary(df, ticker)
    log.info(f"✅ {ticker} pipeline complete → Price: ${summary.get('price')} | RSI: {summary.get('rsi')} | Signal: {summary.get('macd_signal')}")
    return summary


def get_all_etf_data() -> dict:
    """
    Run the full data pipeline for ALL ETFs in the watchlist.
    Saves a JSON snapshot to disk for the dashboard to read.

    Returns:
        Dict of {ticker: data_dict} for all ETFs
    """
    log.info(f"🌸 Starting data cycle for: {', '.join(WATCHLIST)}")
    results = {}

    for ticker in WATCHLIST:
        results[ticker] = get_market_data(ticker)
        time.sleep(0.5)  # Be polite to Yahoo Finance API

    # Save snapshot to disk (Module 4 dashboard reads this)
    snapshot = {
        "fetched_at":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fetched_at_aest": datetime.now(ADELAIDE_TZ).strftime("%Y-%m-%d %H:%M %Z"),
        "market_open":     is_market_open(),
        "data":            results
    }
    snapshot_path = os.path.join(OUTPUT_DIR, "latest_data.json")
    with open(snapshot_path, "w") as f:
        json.dump(snapshot, f, indent=2, default=str)

    log.info(f"💾 Snapshot saved → {snapshot_path}")
    log.info(f"✅ Data cycle complete for {len(results)} ETFs")
    return results


# ─────────────────────────────────────────────
# SECTION 6: AUTOMATIC SCHEDULER
# ─────────────────────────────────────────────

def scheduled_cycle():
    """
    Called automatically by the scheduler.
    Only runs if market is open — skips otherwise.
    """
    schedule_info = get_market_schedule()
    log.info(f"⏰ Scheduled cycle triggered | Adelaide time: {schedule_info.get('current_adelaide')}")

    if not is_market_open():
        log.info(f"⏸  Market closed — skipping data fetch")
        log.info(f"   Next open (Adelaide): {schedule_info.get('next_open_aest', 'Unknown')}")
        return

    log.info("🟢 Market is open — running full data cycle")
    get_all_etf_data()


def run_data_scheduler():
    """
    Start the automatic scheduling loop.
    Runs every FETCH_INTERVAL_MINUTES minutes indefinitely.
    This is the entry point when running Module 1 standalone.
    """
    log.info("=" * 56)
    log.info("  🌸 MIRAI ARCSPHERE · Module 1 · Market Data Engine")
    log.info("=" * 56)
    log.info(f"  Watching:  {', '.join(WATCHLIST)}")
    log.info(f"  Interval:  Every {FETCH_INTERVAL_MINUTES} minutes (market hours only)")
    log.info(f"  Timezone:  Adelaide (ACST/ACDT)")
    log.info("=" * 56)

    # Run once immediately on startup
    log.info("🚀 Running initial data fetch on startup...")
    get_all_etf_data()

    # Schedule recurring runs
    schedule.every(FETCH_INTERVAL_MINUTES).minutes.do(scheduled_cycle)
    log.info(f"📅 Scheduler started — next run in {FETCH_INTERVAL_MINUTES} minutes")

    while True:
        schedule.run_pending()
        time.sleep(30)


# ─────────────────────────────────────────────
# STANDALONE RUNNER
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Quick test — fetch one ETF and print the result
        print("\n🧪 Running Module 1 quick test...")
        data = get_market_data("SPY")
        print(json.dumps(data, indent=2, default=str))
        print("\n✅ Module 1 test complete")
    else:
        # Start the full scheduler
        run_data_scheduler()
