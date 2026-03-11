"""
╔══════════════════════════════════════════════════════════╗
║     MIRAI ARCSPHERE · 未来アークスフィア                   ║
║     Module 2 — AI Analysis Engine (Groq LPU)             ║
║     Version: 2.0.0                                       ║
║     Status:  ✅ Active                                   ║
╚══════════════════════════════════════════════════════════╝

PURPOSE:
  The brain of Mirai ArcSphere. Takes market data from Module 1,
  sends it to Groq's LPU-powered API for ultra-fast analysis,
  and returns structured BUY/SELL/HOLD signals.

WHY GROQ:
  - LPU hardware = 300+ tokens/sec (vs ~100 on GPU clouds)
  - Free tier with generous rate limits (no credit card needed)
  - OpenAI-compatible API = easy to code with
  - Sub-second response = critical for algorithmic trading latency

WHAT THIS MODULE PROVIDES:
  - analyse_ticker(data)       → AI signal for one ETF
  - analyse_all(all_data)      → AI signals for all ETFs
  - get_cached_signals()       → last signals (no API call)
  - should_reanalyse(old, new) → True if price moved enough

DEPENDENCIES:
  pip install groq
"""

import os
import sys
import json
import logging
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Groq API key — get yours free at https://console.groq.com/keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Model to use — Llama 3 70B is fast + capable for structured analysis
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Re-analyse threshold: trigger new AI analysis if price moves more than this %
REANALYSIS_THRESHOLD_PCT = 1.0

# Cache file for signals
SIGNALS_CACHE_FILE = os.path.join(BASE_DIR, "data_snapshots", "signals_cache.json")

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [MODULE-2]  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(BASE_DIR, "logs", "module2.log"), mode="a", encoding="utf-8")
    ]
)
log = logging.getLogger("module2")


# ─────────────────────────────────────────────
# SECTION 1: GROQ AI ANALYSIS
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert ETF trading analyst for an automated trading system called Mirai ArcSphere.
You will receive technical indicator data for an ETF and must return EXACTLY one JSON object.

RULES:
1. Return ONLY valid JSON — no markdown, no explanation, no code fences.
2. Use the exact field names shown below.
3. All numbers must be plain numbers (no strings).
4. signal must be exactly "BUY", "SELL", or "HOLD".
5. risk must be exactly "LOW", "MEDIUM", or "HIGH".
6. tf (timeframe) must be exactly "SHORT", "MEDIUM", or "LONG".
7. conf (confidence) must be an integer between 50 and 95.
8. reason must be 2 concise sentences maximum.
9. risks must be an array of 2 short risk factors.

REQUIRED JSON FORMAT:
{"signal":"BUY","conf":74,"risk":"MEDIUM","entry":531.00,"exit":545.00,"stop":518.00,"tf":"MEDIUM","reason":"Two sentences.","risks":["risk1","risk2"]}"""


def analyse_ticker(ticker_data: dict) -> dict:
    """
    Send one ETF's data to Groq for ultra-fast AI analysis.

    Args:
        ticker_data: Dict from Module 1's generate_signal_summary()

    Returns:
        Dict with signal, confidence, risk, entry/exit/stop, reasoning
    """
    ticker = ticker_data.get("ticker", "UNKNOWN")

    if not GROQ_API_KEY:
        log.warning(f"⚠ No GROQ_API_KEY set — returning technical-only signal for {ticker}")
        log.info(f"  Get your free key at: https://console.groq.com/keys")
        return _placeholder_signal(ticker, ticker_data)

    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        # Build concise data summary for the prompt
        prompt = f"""Analyse this {ticker} ETF data and return your trading signal as JSON:

Price: ${ticker_data.get('price')} (prev: ${ticker_data.get('prev_close')}, change: {ticker_data.get('daily_change_pct')}%)
RSI-14: {ticker_data.get('rsi')} ({ticker_data.get('rsi_signal')})
MACD: {ticker_data.get('macd_signal')} (histogram: {ticker_data.get('macd_histogram')})
Bollinger: {ticker_data.get('bb_signal')} (position: {ticker_data.get('bb_pct')})
SMA-20: {'ABOVE' if ticker_data.get('above_sma20') else 'BELOW'} (${ticker_data.get('sma_20')})
SMA-50: {'ABOVE' if ticker_data.get('above_sma50') else 'BELOW'} (${ticker_data.get('sma_50')})
ADX: {ticker_data.get('adx')}
Stochastic: K={ticker_data.get('stoch_k')} D={ticker_data.get('stoch_d')}
ATR-14: {ticker_data.get('atr_14')}
Volume ratio: {ticker_data.get('vol_ratio')}x average
Golden cross: {ticker_data.get('golden_cross')}

Recent 5-day data:
{ticker_data.get('recent_5d', 'N/A')}"""

        log.info(f"🧠 Sending {ticker} to Groq ({GROQ_MODEL}) for analysis...")

        import time
        start = time.time()

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3,  # Low temp for consistent structured output
        )

        elapsed = time.time() - start
        raw_text = response.choices[0].message.content.strip()

        # Log speed metrics
        usage = response.usage
        if usage:
            tps = usage.completion_tokens / elapsed if elapsed > 0 else 0
            log.info(f"⚡ Groq response in {elapsed:.2f}s | {usage.completion_tokens} tokens | {tps:.0f} tok/s")
        else:
            log.info(f"⚡ Groq response in {elapsed:.2f}s")

        log.info(f"📨 Response for {ticker}: {raw_text[:120]}...")

        # Parse the JSON response
        signal = _parse_signal(raw_text, ticker)
        signal["ticker"] = ticker
        signal["analysed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        signal["price_at_analysis"] = ticker_data.get("price")
        signal["model"] = GROQ_MODEL
        signal["latency_ms"] = round(elapsed * 1000)

        log.info(f"✅ {ticker}: {signal['signal']} ({signal['conf']}% confidence, {signal['risk']} risk) in {signal['latency_ms']}ms")
        return signal

    except Exception as e:
        log.error(f"❌ Groq analysis failed for {ticker}: {e}")
        return _placeholder_signal(ticker, ticker_data)


def _parse_signal(raw_text: str, ticker: str) -> dict:
    """Parse Groq's JSON response, handling common formatting issues."""
    # Remove markdown fences if present
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        log.warning(f"⚠ Failed to parse Groq response for {ticker}, using technical signal")
        return _placeholder_signal(ticker, {})

    # Validate required fields
    required = ["signal", "conf", "risk", "entry", "exit", "stop", "tf", "reason", "risks"]
    for field in required:
        if field not in data:
            log.warning(f"⚠ Missing field '{field}' in Groq response for {ticker}")
            data.setdefault(field, None)

    # Clamp confidence
    if isinstance(data.get("conf"), (int, float)):
        data["conf"] = max(50, min(95, int(data["conf"])))

    return data


def _placeholder_signal(ticker: str, data: dict) -> dict:
    """Generate a reasonable placeholder signal from technical data alone."""
    rsi = data.get("rsi", 50)
    macd_sig = data.get("macd_signal", "NEUTRAL")

    if macd_sig == "BULLISH" and rsi and rsi < 70:
        signal, conf = "BUY", 62
    elif macd_sig == "BEARISH" and rsi and rsi > 30:
        signal, conf = "SELL", 58
    else:
        signal, conf = "HOLD", 55

    price = data.get("price", 0)
    return {
        "ticker": ticker,
        "signal": signal,
        "conf": conf,
        "risk": "MEDIUM",
        "entry": round(price * 0.998, 2) if price else None,
        "exit": round(price * 1.03, 2) if price else None,
        "stop": round(price * 0.97, 2) if price else None,
        "tf": "MEDIUM",
        "reason": f"Auto-generated from technical indicators. MACD is {macd_sig}, RSI at {rsi}.",
        "risks": ["No AI analysis available", "Based on indicators only"],
        "analysed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "price_at_analysis": price,
        "is_placeholder": True,
        "model": "technical-only",
        "latency_ms": 0,
    }


# ─────────────────────────────────────────────
# SECTION 2: BATCH ANALYSIS
# ─────────────────────────────────────────────

def analyse_all(all_data: dict) -> dict:
    """
    Run AI analysis on all ETFs.

    Args:
        all_data: Dict of {ticker: data_dict} from Module 1

    Returns:
        Dict of {ticker: signal_dict}
    """
    log.info(f"🧠 Starting AI analysis for {len(all_data)} tickers via Groq...")
    signals = {}
    total_latency = 0

    for ticker, data in all_data.items():
        if data.get("error"):
            log.warning(f"⏭ Skipping {ticker} — data has errors")
            signals[ticker] = _placeholder_signal(ticker, data)
            continue
        signal = analyse_ticker(data)
        signals[ticker] = signal
        total_latency += signal.get("latency_ms", 0)

    # Cache results
    _save_cache(signals)
    log.info(f"✅ AI analysis complete for {len(signals)} tickers | Total: {total_latency}ms")
    return signals


# ─────────────────────────────────────────────
# SECTION 3: CACHING & RE-ANALYSIS LOGIC
# ─────────────────────────────────────────────

def get_cached_signals() -> dict:
    """Load the last cached signals without making API calls."""
    try:
        if os.path.exists(SIGNALS_CACHE_FILE):
            with open(SIGNALS_CACHE_FILE, "r") as f:
                return json.load(f)
    except Exception as e:
        log.warning(f"⚠ Failed to load signal cache: {e}")
    return {}


def _save_cache(signals: dict):
    """Save signals to cache file."""
    try:
        os.makedirs(os.path.dirname(SIGNALS_CACHE_FILE), exist_ok=True)
        cache = {
            "cached_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "engine": "groq",
            "model": GROQ_MODEL,
            "signals": signals,
        }
        with open(SIGNALS_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2, default=str)
        log.info(f"💾 Signals cached → {SIGNALS_CACHE_FILE}")
    except Exception as e:
        log.error(f"❌ Failed to save signal cache: {e}")


def should_reanalyse(old_data: dict, new_data: dict) -> bool:
    """
    Check if price has moved enough to warrant re-analysis.

    Args:
        old_data: Previous ticker data (or cached signal with price_at_analysis)
        new_data: Fresh ticker data from Module 1

    Returns:
        True if price moved more than REANALYSIS_THRESHOLD_PCT
    """
    old_price = old_data.get("price_at_analysis") or old_data.get("price", 0)
    new_price = new_data.get("price", 0)

    if not old_price or not new_price:
        return True  # No previous data — always analyse

    change_pct = abs((new_price - old_price) / old_price) * 100
    should = change_pct >= REANALYSIS_THRESHOLD_PCT

    if should:
        log.info(f"📈 Price moved {change_pct:.2f}% (>{REANALYSIS_THRESHOLD_PCT}%) — re-analysis triggered")
    else:
        log.info(f"📊 Price moved {change_pct:.2f}% (<{REANALYSIS_THRESHOLD_PCT}%) — using cached signal")

    return should


# ─────────────────────────────────────────────
# STANDALONE RUNNER
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("\n🧪 Running Module 2 quick test (Groq LPU)...")
        print(f"   Model: {GROQ_MODEL}")
        print(f"   API Key: {'✅ Set' if GROQ_API_KEY else '❌ Not set — will use technical-only signals'}")

        # Load latest data from Module 1
        data_file = os.path.join(BASE_DIR, "data_snapshots", "latest_data.json")
        if os.path.exists(data_file):
            with open(data_file, "r") as f:
                snapshot = json.load(f)
            all_data = snapshot.get("data", {})

            if "SPY" in all_data:
                print(f"\n📥 Loaded SPY data: ${all_data['SPY'].get('price')}")
                signal = analyse_ticker(all_data["SPY"])
                print(f"\n🧠 AI Signal:")
                print(json.dumps(signal, indent=2))
                if signal.get("latency_ms"):
                    print(f"\n⚡ Groq latency: {signal['latency_ms']}ms")
            else:
                print("⚠ No SPY data found in latest_data.json")
        else:
            print(f"⚠ No data file found at {data_file}")
            print("   Run 'python module1_market_data.py test' first")

        print("\n✅ Module 2 test complete")
    else:
        print("Usage: python module2_ai_analysis.py test")
        print("\nBefore running, set your Groq API key:")
        print("  $env:GROQ_API_KEY = 'your-key-here'  (PowerShell)")
        print("  Get your free key at: https://console.groq.com/keys")
