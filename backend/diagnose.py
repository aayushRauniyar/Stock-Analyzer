#!/usr/bin/env python3
"""
MIRAI ARCSPHERE — Backend & Alpaca API Diagnostic
Checks: Python env, required packages, Alpaca API keys, backend server, all endpoints
"""
import os, sys, json, time
from datetime import datetime

ORANGE = "\033[33m"
GREEN  = "\033[32m"
RED    = "\033[31m"
CYAN   = "\033[36m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):  print(f"  {GREEN}✅ {msg}{RESET}")
def fail(msg):print(f"  {RED}❌ {msg}{RESET}")
def warn(msg):print(f"  {ORANGE}⚠  {msg}{RESET}")
def info(msg):print(f"  {CYAN}ℹ  {msg}{RESET}")
def hdr(msg): print(f"\n{BOLD}{ORANGE}{'─'*60}{RESET}\n{BOLD} {msg}{RESET}\n{'─'*60}")

print(f"\n{BOLD}{'='*60}")
print("  MIRAI ARCSPHERE — BACKEND & ALPACA DIAGNOSTIC")
print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*60}{RESET}\n")

results = {}

# ─── 1. Python version ────────────────────────────────────────────────────────
hdr("1. PYTHON ENVIRONMENT")
pyver = sys.version.split()[0]
if sys.version_info >= (3, 10):
    ok(f"Python {pyver}")
    results["python"] = True
else:
    fail(f"Python {pyver} — requires 3.10+")
    results["python"] = False


# ─── 2. Required packages ─────────────────────────────────────────────────────
hdr("2. REQUIRED PACKAGES")
required = {
    "flask": "flask",
    "flask_cors": "flask-cors",
    "requests": "requests",
    "yfinance": "yfinance",
    "pandas": "pandas",
    "numpy": "numpy",
    "ta": "ta",
    "pytz": "pytz",
    "groq": "groq",
}

all_pkgs_ok = True
for mod, pkg in required.items():
    try:
        m = __import__(mod)
        ver = getattr(m, "__version__", "?")
        ok(f"{pkg} ({ver})")
    except ImportError:
        fail(f"{pkg} — NOT INSTALLED  →  pip install {pkg}")
        all_pkgs_ok = False

# Check alpaca packages separately (multiple possible names)
alpaca_ok = False
for mod in ["alpaca", "alpaca_trade_api", "alpaca.trading"]:
    try:
        __import__(mod)
        ok(f"alpaca SDK (module: {mod})")
        alpaca_ok = True
        break
    except ImportError:
        pass
if not alpaca_ok:
    fail("alpaca SDK — NOT INSTALLED  →  pip install alpaca-trade-api")
    all_pkgs_ok = False

results["packages"] = all_pkgs_ok


# ─── 3. Alpaca API credentials ────────────────────────────────────────────────
hdr("3. ALPACA API CREDENTIALS")
api_key    = os.getenv("ALPACA_API_KEY", "")
secret_key = os.getenv("ALPACA_SECRET_KEY", "")
base_url   = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

# Also try loading from config.py
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL
    if not api_key:    api_key    = ALPACA_API_KEY
    if not secret_key: secret_key = ALPACA_SECRET_KEY
    base_url = ALPACA_BASE_URL
    info("Loaded config.py")
except Exception as e:
    warn(f"Could not load config.py: {e}")

# Mask keys for display
def mask(k): return k[:6] + "****" + k[-4:] if len(k) > 12 else ("(empty)" if not k else "****")

info(f"ALPACA_API_KEY    = {mask(api_key)}")
info(f"ALPACA_SECRET_KEY = {mask(secret_key)}")
info(f"ALPACA_BASE_URL   = {base_url}")

placeholder_keys = ["YOUR_ALPACA", "your_alpaca", "PLACEHOLDER", ""]
key_is_real = api_key and not any(api_key.startswith(p) for p in placeholder_keys)
sec_is_real = secret_key and not any(secret_key.startswith(p) for p in placeholder_keys)

if key_is_real and sec_is_real:
    ok("API key and secret look real (non-placeholder)")
    results["credentials_set"] = True
else:
    fail("API key / secret are placeholder values — real keys NOT configured")
    warn("Set them as environment variables:")
    warn("  $env:ALPACA_API_KEY='AK...'")
    warn("  $env:ALPACA_SECRET_KEY='sk...'")
    results["credentials_set"] = False


# ─── 4. Test Alpaca API connection ───────────────────────────────────────────
hdr("4. ALPACA API CONNECTIVITY TEST")
alpaca_connected = False

if key_is_real and sec_is_real:
    try:
        import requests as req
        headers = {
            "APCA-API-KEY-ID":     api_key,
            "APCA-API-SECRET-KEY": secret_key,
        }
        r = req.get(f"{base_url}/v2/account", headers=headers, timeout=8)
        if r.status_code == 200:
            acct = r.json()
            ok(f"Alpaca CONNECTED — Account: {acct.get('account_number', '?')}")
            ok(f"  Status:      {acct.get('status', '?')}")
            ok(f"  Equity:      ${float(acct.get('equity', 0)):,.2f}")
            ok(f"  Cash:        ${float(acct.get('cash', 0)):,.2f}")
            ok(f"  Buying Power:${float(acct.get('buying_power', 0)):,.2f}")
            ok(f"  Paper trading: {'YES' in base_url.upper() or 'paper' in base_url}")
            alpaca_connected = True
        elif r.status_code == 401:
            fail(f"Alpaca returned 401 UNAUTHORIZED — Invalid API keys")
        elif r.status_code == 403:
            fail(f"Alpaca returned 403 FORBIDDEN — Check key permissions")
        else:
            fail(f"Alpaca returned HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        fail(f"Alpaca connection failed: {e}")
else:
    warn("Skipping live connection test — no real keys configured")
results["alpaca_connected"] = alpaca_connected


# ─── 5. Test yfinance (fallback data source) ──────────────────────────────────
hdr("5. YFINANCE FALLBACK CONNECTION TEST")
try:
    import yfinance as yf
    ticker = yf.Ticker("SPY")
    hist = ticker.history(period="5d")
    if not hist.empty:
        latest = hist["Close"].iloc[-1]
        ok(f"yfinance connected — SPY latest close: ${latest:.2f}")
        results["yfinance"] = True
    else:
        warn("yfinance returned empty data (possible rate-limit or no internet)")
        results["yfinance"] = False
except Exception as e:
    fail(f"yfinance failed: {e}")
    results["yfinance"] = False


# ─── 6. Test backend server ───────────────────────────────────────────────────
hdr("6. BACKEND SERVER (localhost:5000)")
try:
    import requests as req
    r = req.get("http://localhost:5000/api/market-data", timeout=5)
    if r.status_code == 200:
        data = r.json()
        ok(f"Backend responding — HTTP {r.status_code}")
        if "data" in data:
            ok(f"  Tickers available: {list(data['data'].keys())}")
        if "fetched_at_aest" in data:
            ok(f"  Last fetch: {data['fetched_at_aest']}")
        results["backend"] = True
    elif r.status_code == 404:
        warn(f"Backend running but no market data (run a refresh): {r.json()}")
        results["backend"] = "no_data"
    else:
        fail(f"Backend returned HTTP {r.status_code}")
        results["backend"] = False
except Exception as e:
    fail(f"Backend NOT reachable: {e}")
    warn("Start backend:  cd backend && python server.py")
    results["backend"] = False


# ─── 7. Test all API endpoints ────────────────────────────────────────────────
hdr("7. API ENDPOINTS COVERAGE")
endpoints = [
    ("GET",  "/api/market-data",       "Market data"),
    ("GET",  "/api/signals",           "AI signals"),
    ("GET",  "/api/positions",         "Positions"),
    ("GET",  "/api/portfolio",         "Portfolio"),
    ("GET",  "/api/tax-log",           "Tax log"),
    ("GET",  "/api/market-status",     "Market status"),
]
if results.get("backend"):
    import requests as req
    for method, path, label in endpoints:
        try:
            url = f"http://localhost:5000{path}"
            r = req.get(url, timeout=5) if method == "GET" else req.post(url, timeout=5)
            code = r.status_code
            if code in (200, 201):
                ok(f"{label:20s} {method} {path} → {code}")
            elif code == 404:
                warn(f"{label:20s} {method} {path} → {code} (no cached data)")
            else:
                fail(f"{label:20s} {method} {path} → {code}")
        except Exception as e:
            fail(f"{label:20s} {method} {path} → ERROR: {e}")
else:
    warn("Skipping endpoint tests — backend not reachable")


# ─── SUMMARY ─────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{'='*60}")
print("  DIAGNOSTIC SUMMARY")
print(f"{'='*60}{RESET}")

checks = [
    ("Python env",         results.get("python")),
    ("Packages installed", results.get("packages")),
    ("Alpaca keys set",    results.get("credentials_set")),
    ("Alpaca API live",    results.get("alpaca_connected")),
    ("yfinance fallback",  results.get("yfinance")),
    ("Backend server",     results.get("backend")),
]

all_ok = True
for label, status in checks:
    if status is True:
        ok(f"{label}")
    elif status == "no_data":
        warn(f"{label} — running but no snapshot data yet")
        all_ok = False
    elif status is False:
        fail(f"{label}")
        all_ok = False
    else:
        warn(f"{label} — not checked")

print()
if all_ok:
    print(f"{GREEN}{BOLD}  ALL CHECKS PASSED — System ready ✅{RESET}")
else:
    print(f"{RED}{BOLD}  SOME CHECKS FAILED — See issues above ❌{RESET}")
print(f"{'='*60}\n")
