"""
╔══════════════════════════════════════════════════════════╗
║     MIRAI ARCSPHERE · 未来アークスフィア                   ║
║     Module 1 — Market Data Engine (v2.0)                 ║
║     Status:  ✅ Alpaca + yfinance Dual Source            ║
╚══════════════════════════════════════════════════════════╝

PURPOSE:
  The eyes of Mirai ArcSphere. Fetches real-time and
  historical ETF price data via dual sources (Alpaca + yfinance),
  streams live bars via Alpaca WebSocket, calculates technical
  indicators, detects market hours, and schedules automatic cycles.

ENHANCEMENTS (v2.0):
  ✅ Alpaca Historical Bars API (primary) + yfinance (fallback)
  ✅ Alpaca WebSocket real-time bar streaming
  ✅ Price drift detection (alerts if Alpaca ≠ yfinance >0.5%)
  ✅ Auto-reanalysis trigger (>1% price move detected)
  ✅ Thread-safe SSE queue for dashboard real-time updates

DEPENDENCIES:
  pip install yfinance ta pandas numpy alpaca-trade-api schedule pytz websocket-client
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
import threading
import queue
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

# Alpaca API configuration
ALPACA_API_KEY    = os.getenv("APCA_API_KEY_ID",     "YOUR_ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("APCA_API_SECRET_KEY", "YOUR_ALPACA_SECRET_KEY")
ALPACA_BASE_URL   = os.getenv("APCA_API_BASE_URL", "https://paper-api.alpaca.markets/v2")

# Price drift threshold (%) — alerts if Alpaca price differs from yfinance by this much
PRICE_DRIFT_THRESHOLD_PCT = 0.5

# Price move threshold (%) — triggers Module 2 re-analysis if price moves >1%
REANALYSIS_THRESHOLD_PCT = 1.0

# Output folder for data snapshots
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data_snapshots")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# GLOBAL STATE: Price tracking & SSE queue
# ─────────────────────────────────────────────

# Track last known prices for re-analysis trigger
last_prices = {ticker: None for ticker in WATCHLIST}
last_analysis_prices = {ticker: None for ticker in WATCHLIST}

# Thread-safe queue for broadcasting price updates to server.py (SSE)
sse_event_queue = queue.Queue()
sse_lock = threading.Lock()

# WebSocket connection state
websocket_connection = None
websocket_thread = None

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
        logging.FileHandler(os.path.join(BASE_DIR, "logs", "module1.log"), mode="a", encoding="utf-8")
    ]
)
log = logging.getLogger("module1")
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)


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
# SECTION 2: DATA FETCHING (DUAL SOURCE)
# ─────────────────────────────────────────────

def fetch_alpaca_historical(ticker: str, days: int = HISTORY_DAYS) -> pd.DataFrame:
    """
    Fetch historical OHLCV bars from Alpaca Historical Bars API.
    
    Args:
        ticker: ETF symbol e.g. "SPY"
        days:   Number of calendar days of history
    
    Returns:
        DataFrame with OHLCV columns, or empty DataFrame on failure
    """
    try:
        import alpaca_trade_api as tradeapi
        api = tradeapi.REST(ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL)
        
        end_time = datetime.now(MARKET_TZ)
        start_time = end_time - timedelta(days=days)
        
        log.info(f"📥 Fetching {days}d Alpaca bars for {ticker} ({start_time.date()} → {end_time.date()})")
        
        bars = api.get_bars(
            ticker,
            timeframe="day",
            start=start_time.isoformat(),
            end=end_time.isoformat(),
            adjustment="raw"
        )
        
        if not bars.df.empty:
            df = bars.df.copy()
            df.index = pd.to_datetime(df.index).normalize()  # Ensure date-only index
            log.info(f"✅ Alpaca: {ticker} → {len(df)} bars ({df.index[0].date()} → {df.index[-1].date()})")
            return df
        else:
            log.warning(f"⚠ Alpaca: No bars returned for {ticker}")
            return pd.DataFrame()
            
    except Exception as e:
        log.warning(f"⚠ Alpaca Historical API unavailable for {ticker}: {e}")
        return pd.DataFrame()


def fetch_yfinance_data(ticker: str, days: int = HISTORY_DAYS) -> pd.DataFrame:
    """
    Fetch historical OHLCV data from Yahoo Finance (fallback).
    
    Args:
        ticker: ETF symbol e.g. "SPY"
        days:   Number of calendar days of history
    
    Returns:
        DataFrame with OHLCV columns, or empty DataFrame on failure
    """
    try:
        log.info(f"📥 Fetching {days}d yfinance history for {ticker}...")
        period = f"{days}d"
        df = yf.Ticker(ticker).history(period=period, interval="1d")
        
        if df.empty:
            log.warning(f"⚠ yfinance: No data returned for {ticker}")
            return pd.DataFrame()
        
        df.index = df.index.tz_localize(None)
        log.info(f"✅ yfinance: {ticker} → {len(df)} bars ({df.index[0].date()} → {df.index[-1].date()})")
        return df
        
    except Exception as e:
        log.error(f"❌ yfinance failed for {ticker}: {e}")
        return pd.DataFrame()


def compare_data_sources(alpaca_df: pd.DataFrame, yfinance_df: pd.DataFrame, ticker: str) -> dict:
    """
    Compare closing prices between Alpaca and yfinance.
    Alert if drift exceeds PRICE_DRIFT_THRESHOLD_PCT.
    
    Returns:
        Dict with comparison stats
    """
    if alpaca_df.empty or yfinance_df.empty:
        return {"status": "incomplete", "reason": "one or both sources missing"}
    
    # Get common dates
    common_dates = alpaca_df.index.intersection(yfinance_df.index)
    if len(common_dates) == 0:
        return {"status": "no_overlap", "reason": "no common dates"}
    
    alpaca_close = alpaca_df.loc[common_dates, "Close"]
    yfinance_close = yfinance_df.loc[common_dates, "Close"]
    
    # Calculate percentage drift
    price_diff_pct = ((alpaca_close - yfinance_close) / yfinance_close * 100).abs()
    max_drift = price_diff_pct.max()
    mean_drift = price_diff_pct.mean()
    
    status = "OK"
    if max_drift > PRICE_DRIFT_THRESHOLD_PCT:
        log.warning(f"⚠ DRIFT DETECTED for {ticker}: max={max_drift:.3f}%, mean={mean_drift:.3f}%")
        status = "DRIFT_WARNING"
    else:
        log.info(f"✅ Price drift for {ticker}: max={max_drift:.3f}%, mean={mean_drift:.3f}% (acceptable)")
    
    return {
        "status": status,
        "max_drift_pct": round(max_drift, 3),
        "mean_drift_pct": round(mean_drift, 3),
        "common_dates": len(common_dates)
    }


def fetch_raw_data(ticker: str, days: int = HISTORY_DAYS) -> pd.DataFrame:
    """
    Fetch raw OHLCV data using dual sources: Alpaca (primary) + yfinance (fallback).
    
    Uses Alpaca Historical Bars API if available, falls back to yfinance.
    Compares sources to detect price drift.
    
    Args:
        ticker: ETF symbol e.g. "SPY"
        days:   Number of calendar days of history
    
    Returns:
        DataFrame with OHLCV columns
    """
    log.info(f"🔄 Fetching dual-source data for {ticker}...")
    
    # Try Alpaca first
    alpaca_df = fetch_alpaca_historical(ticker, days)
    
    # Try yfinance as backup
    yfinance_df = fetch_yfinance_data(ticker, days)
    
    # Compare and log drift
    comparison = compare_data_sources(alpaca_df, yfinance_df, ticker)
    
    # Prefer Alpaca if available, else yfinance
    if not alpaca_df.empty:
        log.info(f"✅ Using Alpaca data for {ticker} (comparison: {comparison['status']})")
        return alpaca_df
    elif not yfinance_df.empty:
        log.info(f"⚠ Alpaca unavailable, falling back to yfinance for {ticker}")
        return yfinance_df
    else:
        log.error(f"❌ All data sources failed for {ticker}")
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
        time.sleep(0.5)  # Be polite to APIs

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
# SECTION 5B: PRICE TRACKING & RE-ANALYSIS
# ─────────────────────────────────────────────

def check_reanalysis_needed(ticker: str, current_price: float) -> bool:
    """
    Check if a price move warrants Module 2 re-analysis.
    Compares against last analysis price (not just last price).
    
    Args:
        ticker: ETF symbol
        current_price: Current closing price
    
    Returns:
        True if price moved >REANALYSIS_THRESHOLD_PCT since last analysis
    """
    last_analysis = last_analysis_prices.get(ticker)
    
    if last_analysis is None:
        # First time — set baseline
        last_analysis_prices[ticker] = current_price
        return False
    
    price_move_pct = abs((current_price - last_analysis) / last_analysis * 100)
    
    if price_move_pct > REANALYSIS_THRESHOLD_PCT:
        log.info(f"📈 {ticker}: Price moved {price_move_pct:.2f}% (>{REANALYSIS_THRESHOLD_PCT}%) — triggering re-analysis")
        last_analysis_prices[ticker] = current_price
        return True
    
    return False


def broadcast_price_update(ticker: str, data: dict, should_reanalyse: bool = False):
    """
    Push a price update to the SSE queue for real-time dashboard updates.
    server.py will consume this and broadcast to connected clients.
    
    Args:
        ticker: ETF symbol
        data: Market data dict from get_market_data()
        should_reanalyse: If True, server should trigger Module 2 analysis
    """
    try:
        event = {
            "type": "price_update",
            "ticker": ticker,
            "price": data.get("price"),
            "change_pct": data.get("daily_change_pct"),
            "rsi": data.get("rsi"),
            "macd_signal": data.get("macd_signal"),
            "timestamp": datetime.now().isoformat(),
            "should_reanalyse": should_reanalyse,
        }
        sse_event_queue.put_nowait(event)
    except queue.Full:
        log.warning(f"⚠ SSE queue full, dropping update for {ticker}")


# ─────────────────────────────────────────────
# SECTION 5C: ALPACA WEBSOCKET STREAMING
# ─────────────────────────────────────────────

def on_bar(bar):
    """
    WebSocket callback: Called when a new bar arrives from Alpaca.
    Updates last_prices and triggers re-analysis if needed.
    """
    try:
        ticker = bar.symbol
        price = bar.close
        
        last_prices[ticker] = price
        
        needs_reanalysis = check_reanalysis_needed(ticker, price)
        
        # Fetch full market data and broadcast
        market_data = get_market_data(ticker)
        broadcast_price_update(ticker, market_data, should_reanalyse=needs_reanalysis)
        
        log.info(f"📊 WebSocket: {ticker} → ${price} (reanalyse: {needs_reanalysis})")
    except Exception as e:
        log.error(f"❌ WebSocket callback error: {e}")


def start_websocket_stream():
    """
    Start Alpaca WebSocket connection for real-time bar updates.
    Runs in a background thread.
    
    This streams 1-min bars for our watchlist tickers.
    Falls back gracefully if WebSocket unavailable.
    """
    global websocket_connection, websocket_thread
    
    try:
        import alpaca_trade_api as tradeapi
        from alpaca_trade_api.rest import APIError
        
        log.info(f"🔌 Starting Alpaca WebSocket for: {', '.join(WATCHLIST)}")
        
        conn = tradeapi.StreamConn(
            base_url=ALPACA_BASE_URL,
            key_id=ALPACA_API_KEY,
            secret_key=ALPACA_SECRET_KEY
        )
        
        # Subscribe to bar updates for all tickers
        @conn.on_bars()
        def handle_bars(bars):
            for bar in bars:
                on_bar(bar)
        
        websocket_connection = conn
        conn.run()
        
    except Exception as e:
        log.warning(f"⚠ WebSocket connection failed: {e}")
        log.info(f"   Continuing with fallback polling mode...")
        websocket_connection = None


def ensure_websocket_alive():
    """
    Monitor WebSocket connection. Attempt to restart if it dies.
    Called periodically from the main scheduler loop.
    """
    global websocket_thread
    
    if websocket_thread is None or not websocket_thread.is_alive():
        log.info("🔄 WebSocket thread dead or not started — attempting restart...")
        websocket_thread = threading.Thread(target=start_websocket_stream, daemon=True)
        websocket_thread.start()
        time.sleep(2)


# ─────────────────────────────────────────────
# SECTION 5D: SSE QUEUE INTERFACE FOR SERVER
# ─────────────────────────────────────────────

def get_sse_events(timeout: float = 0.1) -> list:
    """
    Get all pending SSE events from the queue.
    Called by server.py to broadcast to dashboard.
    
    Args:
        timeout: How long to wait for events
    
    Returns:
        List of event dicts
    """
    events = []
    while True:
        try:
            event = sse_event_queue.get(timeout=timeout)
            events.append(event)
        except queue.Empty:
            break
    return events


# ─────────────────────────────────────────────
# SECTION 6: AUTOMATIC SCHEDULER
# ─────────────────────────────────────────────

def scheduled_cycle():
    """
    Called automatically by the scheduler.
    Only runs if market is open — skips otherwise.
    Ensures WebSocket is alive.
    """
    schedule_info = get_market_schedule()
    log.info(f"⏰ Scheduled cycle triggered | Adelaide time: {schedule_info.get('current_adelaide')}")

    # Monitor WebSocket connection
    ensure_websocket_alive()

    if not is_market_open():
        log.info(f"⏸  Market closed — skipping data fetch")
        log.info(f"   Next open (Adelaide): {schedule_info.get('next_open_aest', 'Unknown')}")
        return

    log.info("🟢 Market is open — running full data cycle")
    get_all_etf_data()


def run_data_scheduler():
    """
    Start the automatic scheduling loop with WebSocket streaming.
    Runs every FETCH_INTERVAL_MINUTES minutes indefinitely.
    Starts WebSocket in background for real-time updates.
    """
    log.info("=" * 56)
    log.info("  🌸 MIRAI ARCSPHERE · Module 1 · Market Data Engine v2.0")
    log.info("=" * 56)
    log.info(f"  Watching:  {', '.join(WATCHLIST)}")
    log.info(f"  Interval:  Every {FETCH_INTERVAL_MINUTES} minutes (market hours only)")
    log.info(f"  Drift Threshold: {PRICE_DRIFT_THRESHOLD_PCT}%")
    log.info(f"  Reanalysis Threshold: {REANALYSIS_THRESHOLD_PCT}%")
    log.info(f"  Timezone:  Adelaide (ACST/ACDT)")
    log.info("=" * 56)

    # Start WebSocket in background thread
    log.info("🔌 Starting Alpaca WebSocket listener...")
    global websocket_thread
    websocket_thread = threading.Thread(target=start_websocket_stream, daemon=True)
    websocket_thread.start()
    time.sleep(2)

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
