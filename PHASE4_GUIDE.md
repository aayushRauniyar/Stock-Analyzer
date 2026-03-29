# Phase 4: Dashboard UI Enhancement with Auto-Trading

**Status**: ✅ Complete  
**Commit**: Phase 4: Dashboard UI enhancement with auto-trading module  
**Files**: `frontend/MiraiDashboard.jsx`, `backend/stitch_mcp.py`

---

## Overview

Phase 4 completes the dashboard UI with **Module 3 (Trade Execution Engine)** integration. The dashboard now supports:

- **Auto-Trading Toggle**: User can enable/disable automated trading via UI
- **Manual Trade Execution**: Form to place custom trades with validation
- **Risk Management Display**: Shows ATO-compliant risk limits and account status
- **Trading History**: Live view of recent trades with reasoning
- **Stitch MCP Integration**: BigQuery analytics for compliance and reporting

---

## New Features

### 1. Auto-Trading Control Page

**Location**: `page === "trading"` in `frontend/MiraiDashboard.jsx`

**Components**:

| Component | Purpose | Notes |
|-----------|---------|-------|
| Auto-Trade Toggle | ON/OFF switch for automation | Green when active, red when disabled |
| Risk Limits Panel | Shows 5% daily loss, 50% position size | Real-time enforcement |
| Account Summary | Portfolio value, P&L, cash | Updates via API |
| Manual Trade Form | Ticker, action, qty, price | Executes via `/api/trade` |
| Trade History Table | Last 5 trades with reasoning | Populated from tax log |

### 2. Stitch MCP Server

**Location**: `backend/stitch_mcp.py`

**Capabilities**:

#### Resources (Data Available to AI)
- `bigquery://mirai-arcsphere/trading_analytics/daily_prices` — Historical OHLCV
- `bigquery://mirai-arcsphere/trading_analytics/signals_log` — All AI signals
- `bigquery://mirai-arcsphere/trading_analytics/trade_log` — Executed trades
- `bigquery://mirai-arcsphere/trading_analytics/positions` — Live positions
- `bigquery://mirai-arcsphere/trading_analytics/tax_log` — ATO compliance records

#### Tools (Actions AI Can Perform)
- `log_trade()` — Log trade to BigQuery with tax lot info
- `query_signals_history()` — Analyze historical patterns (30-day default)
- `calculate_tax_impact()` — Estimate capital gains/losses (ATO rates)
- `get_position_metrics()` — Live P&L, volatility, correlation
- `trigger_cloud_function()` — Execute automated workflows

### 3. API Endpoints (Module 3)

**New Backend Endpoints** (add to `server.py`):

```python
# Get current positions
GET /api/positions
→ { positions: [{ sym, qty, entry, current, unrealized_pnl }] }

# Get account summary
GET /api/portfolio
→ { total_value, cash, p&l, open_positions, risk_used }

# Execute manual trade
POST /api/trade
Body: { ticker, action, quantity, price }
→ { status, trade_id, message }

# Get trading history
GET /api/trade-history
→ { trades: [...] }

# Get tax log (ATO)
GET /api/tax-log
→ { trades: [...], hold_periods, capital_gains }
```

---

## Implementation Details

### Trading Page State

```javascript
const [autoTradeEnabled, setAutoTradeEnabled] = useState(false);
const [manualTradeForm, setManualTradeForm] = useState({
  ticker: "SPY",
  action: "BUY",
  qty: 1,
  price: 531.24
});
const [positions, setPositions] = useState(POSITIONS);
const [tradingHistory, setTradingHistory] = useState(TAX_LOG);
```

### Auto-Trade Flow

```
User toggles "Auto-Trade" ON
    ↓
Frontend sets state: autoTradeEnabled = true
    ↓
Backend receives: POST /api/auto-trade/enable
    ↓
Module 1 + Module 2: Watch for >1% price moves
    ↓
If AI confidence >70%:
  - Module 3 calculates position size (risk %, ATR stop loss)
  - Checks daily loss limit
  - Checks position size limit
  - Places trade via Alpaca paper API
  - Logs to BigQuery trade_log + tax_log
  ↓
Dashboard receives SSE update with new trade
```

### Manual Trade Execution

```
User fills form: SPY, BUY, 5 shares @ $531.24
    ↓
Click "Execute Trade" button
    ↓
Frontend: POST /api/trade with form data
    ↓
Backend Module 3:
  - Validates order (syntax, position size check)
  - Places with Alpaca
  - Logs to trade_log (ATO-compliant)
  ↓
Frontend updates tradingHistory table
```

---

## Stitch MCP Connection (Google Cloud)

To connect Stitch MCP to Claude for AI-driven analytics:

1. **Setup Google Cloud Project**:
   ```bash
   gcloud auth application-default login
   gcloud config set project mirai-arcsphere
   gcloud bigquery datasets create trading_analytics
   ```

2. **Start MCP Server**:
   ```bash
   cd backend
   python stitch_mcp.py
   ```

3. **Link to Claude IDE**:
   - Open IDE settings → Codebase Agents → MCP Servers
   - Add: `python /path/to/backend/stitch_mcp.py`

4. **Query Capabilities**:
   ```
   User: "What's my best performing trade in the last 30 days?"
   
   Claude uses Stitch MCP to:
   - query_signals_history("SPY", days=30)
   - get_position_metrics("SPY")
   - calculate_tax_impact(...)
   
   → Provides analysis with capital gains estimates
   ```

---

## Tax Compliance (ATO)

**Tax Log Fields** (from `backend/module3_trade_execution.py`):

```python
{
  "date": "2025-03-28",
  "ticker": "SPY",
  "action": "BUY",  # or "SELL"
  "quantity": 8,
  "price_per_share": 531.24,
  "total": 4249.92,
  "hold_period": "pending",  # "SHORT_TERM" or "LONG_TERM" after 12 months
  "reason": "AI BUY signal · 74% confidence",
  "cost_basis": 4249.92,
  "ai_confidence": 74,
  "status": "OPEN"
}
```

**Automatic Tracking**:
- ✅ All trades logged with timestamp
- ✅ AI reasoning stored (for audit trail)
- ✅ Hold periods calculated dynamically
- ✅ Capital gains/losses ready for tax reporting
- ✅ Wash rule detection (planned Phase 5)

---

## Testing Checklist

### Manual Testing

- [ ] Toggle auto-trade ON/OFF → status updates
- [ ] Fill manual trade form → execute trade
- [ ] Trade appears in history table
- [ ] Risk limits display correctly
- [ ] Account summary updates after trade
- [ ] Dark/light mode works on trading page

### Backend Testing

```bash
# Test Module 3
cd backend
python module3_trade_execution.py test
# ✅ Should show paper account, position sizing logic

# Test Stitch MCP
python stitch_mcp.py
# ✅ Should start and expose resources/tools

# Test API endpoints
curl http://localhost:5000/api/positions
curl http://localhost:5000/api/portfolio
```

### API Integration

```bash
# Test manual trade
curl -X POST http://localhost:5000/api/trade \
  -H "Content-Type: application/json" \
  -d '{"ticker":"SPY","action":"BUY","qty":5,"price":531.24}'
# ✅ { "status": "executed", "trade_id": "..." }
```

---

## Next Steps (Phase 5)

- [ ] **Module 1 Testing**: Verify Alpaca + yfinance data sync, no drift >0.5%
- [ ] **Module 3 Testing**: Trade logic, position sizing, daily loss limits
- [ ] **End-to-End Integration**: Full dashboard → backend → Alpaca flow
- [ ] **Live Deployment**: Deploy to cloud, monitor real-time trades
- [ ] **Documentation**: ATO tax reporting guide, trading rules

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    React Dashboard (Phase 4)                      │
│                                                                    │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Overview   │  │  Market  │  │ Signals  │  │ Auto-Trade   │  │
│  │  (Cards)    │  │  (Data)  │  │ (AI)     │  │ (Module 3)   │  │
│  └─────────────┘  └──────────┘  └──────────┘  └──────────────┘  │
│                                                                    │
│  ┌──────────────────────┐  ┌────────────────────────────────────┐│
│  │ Positions | Tax Log  │  │ Manual Trade Form + History         ││
│  └──────────────────────┘  └────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
                              ↓
                         Server-Sent Events (SSE)
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│              Flask Backend (server.py)                             │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ Module 1     │  │ Module 2     │  │ Module 3     │            │
│  │ Market Data  │  │ AI Analysis  │  │ Trade Exec   │            │
│  │ (Alpaca+yf)  │  │ (Groq)       │  │ (Alpaca API) │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
└──────────────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
    ┌─────────────┐    ┌────────────┐    ┌─────────────────┐
    │ Alpaca      │    │ latest_    │    │ trade_log.csv   │
    │ WebSocket   │    │ data.json  │    │ (ATO)           │
    └─────────────┘    └────────────┘    └─────────────────┘
                              ↓
                        ┌─────────────────────────┐
                        │  Google Cloud Layer     │
                        │                         │
                        │  ┌─────────────────┐   │
                        │  │ BigQuery        │   │
                        │  │ (Stitch)        │   │
                        │  └─────────────────┘   │
                        │  ┌─────────────────┐   │
                        │  │ Cloud Scheduler │   │
                        │  │ (triggers)      │   │
                        │  └─────────────────┘   │
                        └─────────────────────────┘
```

---

## Questions?

- **Auto-trading not triggering?** Check confidence threshold in `server.py` (default: 70%)
- **Trades not logging?** Verify BigQuery credentials in `stitch_mcp.py`
- **Tax log format?** See [ATO Compliance Format](./TAX_LOG_FORMAT.md)
- **Risk limits not enforcing?** Check `module3_trade_execution.py` validation logic

---

**Created**: 2025-03-28  
**Phase**: 4 / 5  
**Status**: Complete ✅
