# Local Development Setup — Run Mirai ArcSphere Locally

**Status**: Ready to Run  
**Difficulty**: Beginner-Friendly  
**Duration**: 20-30 minutes setup  
**OS**: Works on macOS, Linux, Windows (with WSL recommended)

---

## 🎯 Quick Start (5 minutes)

```bash
# Clone/Navigate to repo
cd Stock-Analyzer

# Terminal 1: Backend
cd backend
pip install -r requirements.txt
python server.py
# Should see: "Running on http://localhost:5000"

# Terminal 2: Frontend  
cd frontend
npm install
npm run dev
# Should see: "Local: http://127.0.0.1:5173/"

# Open browser: http://127.0.0.1:5173/
# Should see: Mirai ArcSphere dashboard 🎉
```

---

## 📋 Prerequisites

### Python 3.10+
```bash
# Check Python version
python --version
# Should be: 3.10.0 or higher

# Install if needed: https://www.python.org/downloads/
```

### Node.js 18+
```bash
# Check Node version
node --version
# Should be: v18.0.0 or higher

# Install if needed: https://nodejs.org/
```

### Git
```bash
# Check Git
git --version
# Should be: 2.0.0 or higher
```

### Virtual Environment (Optional but Recommended)
```bash
# Create virtual env for Python isolation
python -m venv venv

# Activate it
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

---

## STEP 1: Backend Setup (10 minutes)

### 1.1 Navigate to Backend

```bash
cd backend
```

### 1.2 Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Should install:
# ✓ yfinance
# ✓ ta (technical analysis)
# ✓ pandas
# ✓ numpy
# ✓ alpaca-trade-api
# ✓ flask
# ✓ flask-cors
# ✓ anthropic (Claude API)
# ✓ pyarrow
# ... and more

# Verify installation
pip list | grep -E "flask|yfinance|ta|alpaca"
```

### 1.3 Setup Environment Variables

```bash
# Create .env file for local development
cat > .env << EOF
# Environment
ENVIRONMENT=development
FLASK_ENV=development
DEBUG=True
LOG_LEVEL=DEBUG

# Alpaca API (Paper Trading)
APCA_API_KEY_ID=YOUR_ALPACA_KEY_ID
APCA_API_SECRET_KEY=YOUR_ALPACA_SECRET_KEY
APCA_API_BASE_URL=https://paper-api.alpaca.markets

# Claude API (for AI signals)
ANTHROPIC_API_KEY=your_claude_api_key

# Optional: Google Cloud (for Stitch MCP)
GCP_PROJECT=your-gcp-project-id

# Flask
FLASK_SECRET_KEY=dev-secret-key-change-in-production
EOF

# Note: Get Alpaca keys from https://app.alpaca.markets/paper/dashboard/home
# Note: Get Claude key from https://console.anthropic.com/
```

### 1.4 Verify Backend Works

```bash
# Start Flask development server
python server.py

# Expected output:
# * Serving Flask app 'server'
# * Debug mode: on
# * Running on http://127.0.0.1:5000

# Test in another terminal
curl http://localhost:5000/api/market-data
# Should return JSON with market data
```

---

## STEP 2: Frontend Setup (10 minutes)

### 2.1 Navigate to Frontend

```bash
cd frontend
```

### 2.2 Install Node Dependencies

```bash
# Install all npm packages
npm install

# Should install:
# ✓ react
# ✓ react-dom
# ✓ vite
# ✓ @vitejs/plugin-react
# ✓ ... and dev dependencies

# Verify installation
npm list | head -20
```

### 2.3 Verify Vite Config

```bash
# Check vite.config.js has API proxy configured
cat vite.config.js

# Should include:
# server: {
#   proxy: {
#     '/api': {
#       target: 'http://localhost:5000',
#       changeOrigin: true
#     }
#   }
# }
```

### 2.4 Start Frontend Dev Server

```bash
# Start Vite dev server
npm run dev

# Expected output:
# VITE v4.x.x  ready in xxx ms
# ➜  Local:   http://127.0.0.1:5173/
# ➜  Press q to quit

# Note the URL: http://127.0.0.1:5173/
```

---

## STEP 3: Access Dashboard

### 3.1 Open Browser

```bash
# Open in browser
http://127.0.0.1:5173/

# Or click link from Vite output
```

### 3.2 What You Should See

```
✅ Mirai ArcSphere logo (🌸)
✅ Navigation sidebar (Overview, Market, Signals, Auto-Trade, etc.)
✅ Overview page with:
   - Portfolio KPIs (value, P&L, cash, positions)
   - ETF cards (SPY, QQQ, VTI) with live prices
   - Indicator tiles (RSI, MACD, Bollinger)
✅ Dark/Light mode toggle (top right)
✅ Last update timestamp
```

### 3.3 Try Interacting

```
1. Click "🌸 Refresh All" → fetches fresh data
2. Navigate to "Market Data" tab → detailed price table
3. Navigate to "AI Signals" → sees BUY/SELL signals
4. Navigate to "Auto-Trade" → toggle ON/OFF
5. Fill manual trade form → execute trade
6. Navigate to "Tax Log" → see trade history
```

---

## STEP 4: Run Local Tests

### 4.1 Run All Tests

```bash
cd backend

# Test 1: Module 1 (Data integration)
python test_phase5_module1.py
# Should complete in ~30 sec

# Test 2: Module 3 (Trade logic)
python test_phase5_module3.py
# Should complete in ~10 sec

# Test 3: Integration (All endpoints)
python test_phase5_integration.py
# Should complete in ~15 sec
```

### 4.2 Check Test Results

```bash
# View test reports
cat ../logs/phase5_module1_test.json | python -m json.tool
cat ../logs/phase5_module3_test.json | python -m json.tool
cat ../logs/phase5_integration_test.json | python -m json.tool
```

---

## 🏗️ Full Local Architecture

```
Your Computer (localhost)
│
├─── Terminal 1: Backend (Port 5000)
│    │
│    ├─ http://localhost:5000
│    │  ├─ GET  /api/market-data    → Latest prices
│    │  ├─ GET  /api/signals        → AI signals
│    │  ├─ POST /api/refresh        → Fetch + analyze
│    │  ├─ POST /api/trade          → Execute trade
│    │  ├─ GET  /api/positions      → Open trades
│    │  ├─ GET  /api/portfolio      → Account summary
│    │  ├─ GET  /api/stream (SSE)   → Real-time updates
│    │  └─ GET  /api/tax-log        → Trade history
│    │
│    └─ Python Modules:
│       ├─ module1_market_data.py  (Alpaca + yfinance)
│       ├─ module2_ai_analysis.py  (Claude API)
│       ├─ module3_trade_execution.py (Alpaca trading)
│       └─ stitch_mcp.py (BigQuery mocking)
│
├─── Terminal 2: Frontend (Port 5173)
│    │
│    └─ http://127.0.0.1:5173/
│       ├─ React Dashboard (MiraiDashboard.jsx)
│       ├─ Real-time updates via SSE
│       ├─ API calls proxied to localhost:5000
│       └─ Hot reload on code changes
│
└─── External Services (Optional)
     ├─ Alpaca Paper Trading API (for real data)
     └─ Claude API (for AI signals)
```

---

## 🔄 Development Workflow

### Terminal 1: Backend
```bash
cd backend
python server.py

# Auto-reloads on code changes (DEBUG=True)
# View logs in console
# Errors show with full stack trace
```

### Terminal 2: Frontend
```bash
cd frontend
npm run dev

# Auto-reloads on code changes (Vite HMR)
# Fast refresh with preserved state
# Errors show in console + browser
```

### Terminal 3: Optional - Test Suite
```bash
cd backend

# Run tests while developing
python test_phase5_module1.py
python test_phase5_module3.py
python test_phase5_integration.py

# Or run continuously
while true; do
  python test_phase5_integration.py
  sleep 60
done
```

---

## 📊 Sample Data (What You'll See)

### Market Data
```json
{
  "SPY": {
    "price": 531.24,
    "change": 0.50,
    "rsi": 56.2,
    "macd": "BULLISH",
    "sma20": "ABOVE",
    "volume": 68420000
  }
  // ... QQQ, VTI
}
```

### AI Signals
```json
{
  "SPY": {
    "signal": "BUY",
    "confidence": 74,
    "entry": 531.00,
    "exit": 545.00,
    "stop": 518.00,
    "reason": "SMA 20 crossing above SMA 50..."
  }
  // ... QQQ, VTI
}
```

### Positions (After Trading)
```json
{
  "positions": [
    {"sym": "SPY", "qty": 8, "entry": 524.30, "current": 531.24},
    {"sym": "QQQ", "qty": 5, "entry": 448.10, "current": 451.88},
    {"sym": "VTI", "qty": 12, "entry": 275.80, "current": 271.45}
  ]
}
```

---

## 🐛 Troubleshooting

### Issue: "Backend not responding"
```bash
# Check if server is running
ps aux | grep "python server.py"

# If not, start it
cd backend && python server.py

# If still failing, check error:
python server.py 2>&1 | head -20
```

### Issue: "Frontend can't reach backend"
```bash
# Test backend directly
curl http://localhost:5000/api/market-data
# Should return JSON

# If fails, check:
1. Is backend running? (see above)
2. Is it on port 5000? (netstat -an | grep 5000)
3. Check vite.config.js has correct proxy
```

### Issue: "Module not found" (Python)
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or if using venv, make sure it's activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate      # Windows
```

### Issue: "npm ERR! 404"
```bash
# Clear npm cache
npm cache clean --force

# Reinstall
rm -rf node_modules package-lock.json
npm install
```

### Issue: "Port 5000 already in use"
```bash
# Find what's using it
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Kill it (replace PID)
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
FLASK_ENV=development FLASK_APP=server.py python -m flask run --port 5001
```

### Issue: "Alpaca API keys not working"
```bash
# Get keys from: https://app.alpaca.markets/paper/dashboard/home
# They're under: Settings → API Keys

# Test connection
python -c "
from alpaca.data.historical import StockHistoricalDataClient
client = StockHistoricalDataClient('YOUR_KEY', 'YOUR_SECRET')
print('✅ Connected!')
"

# If fails, verify:
1. Using PAPER trading keys (not live)
2. Keys have correct permissions
3. Keys are not expired
```

### Issue: "Claude API not responding"
```bash
# Get API key from: https://console.anthropic.com/
# Add to .env: ANTHROPIC_API_KEY=your_key

# Test connection
python -c "
from anthropic import Anthropic
client = Anthropic()
msg = client.messages.create(model='claude-3-5-sonnet-20241022', max_tokens=100, messages=[{'role': 'user', 'content': 'hi'}])
print('✅ Connected!')
"
```

---

## 📁 Project Structure (Locally)

```
Stock-Analyzer/
├── backend/
│   ├── server.py                    ← Start: python server.py
│   ├── module1_market_data.py      
│   ├── module2_ai_analysis.py      
│   ├── module3_trade_execution.py  
│   ├── stitch_mcp.py               
│   ├── requirements.txt             ← pip install -r requirements.txt
│   ├── test_phase5_module1.py      ← python test_phase5_module1.py
│   ├── test_phase5_module3.py      ← python test_phase5_module3.py
│   ├── test_phase5_integration.py  ← python test_phase5_integration.py
│   ├── .env                        ← Local config (create this)
│   └── logs/
│       ├── phase5_module1_test.json
│       ├── phase5_module3_test.json
│       └── phase5_integration_test.json
│
├── frontend/
│   ├── index.html                  
│   ├── main.jsx                    
│   ├── MiraiDashboard.jsx          ← Main dashboard component
│   ├── vite.config.js              ← Has /api proxy to localhost:5000
│   ├── package.json                ← npm install
│   └── src/
│       └── ... (React components)
│
├── data_snapshots/
│   └── latest_data.json            ← Live market data cache
│
└── logs/
    └── (Test reports & trade logs)
```

---

## ⚡ Performance Tips

### Backend
- Runs fast on laptop (Python 3.10+)
- API calls <200ms typically
- WebSocket updates real-time

### Frontend
- Vite dev server super fast (HMR <100ms)
- Hot reload on every save
- No refresh needed

### Both Together
- Full app loads in <2 seconds
- Responsive to all interactions
- Can run 24/7 for testing

---

## 🔄 Common Development Tasks

### Add New API Endpoint
```python
# In backend/server.py
@app.route('/api/new-endpoint')
def new_endpoint():
    return jsonify({"result": "data"})

# Test: curl http://localhost:5000/api/new-endpoint
```

### Update Dashboard UI
```javascript
// In frontend/MiraiDashboard.jsx
function NewComponent() {
  return <div>New feature</div>
}

// Saves automatically → HMR updates browser
```

### Run Tests While Developing
```bash
# Terminal 3: Loop tests
cd backend
while true; do
  clear
  python test_phase5_integration.py
  echo "Test complete. Waiting 60 sec..."
  sleep 60
done
```

### Debug Backend
```python
# Add debug print in server.py
@app.route('/api/debug')
def debug():
    print("DEBUG: Entering debug endpoint")  # Shows in Terminal 1
    return {"status": "ok"}
```

### View Backend Logs
```bash
# Terminal 1 output shows all Flask logs
# Also writes to: backend/logs/
tail -f backend/logs/*.log
```

---

## 🧪 Testing Workflow

### Unit Tests
```bash
cd backend
python test_phase5_module1.py  # Data tests
python test_phase5_module3.py  # Trade tests
```

### Integration Tests
```bash
cd backend
python test_phase5_integration.py  # Full API
```

### Manual Testing
```bash
# In browser
http://127.0.0.1:5173/

# Try:
1. Click "Refresh All" → loads data
2. Toggle "Auto-Trade" ON/OFF
3. Fill trade form → execute
4. Check "Tax Log" for history
```

---

## 📊 Monitoring Local System

### Check Backend Health
```bash
# In Terminal 1, you should see:
# - Incoming requests logged
# - Data fetch logs
# - API response times
```

### Check Frontend Status
```bash
# In Terminal 2, you should see:
# - HMR updates
# - Component re-renders
# - Network requests to /api/*
```

### Check in Browser Console
```javascript
// Open DevTools (F12) → Console
// Should not show any errors
// Network tab shows:
// - GET /api/market-data ✅ 200
// - GET /api/signals ✅ 200
// - POST /api/refresh ✅ 200
```

---

## 🎓 What Each Component Does (Locally)

### Backend (Terminal 1)
- **Module 1**: Fetches real market data from Alpaca + yfinance
- **Module 2**: Sends data to Claude for AI signal analysis
- **Module 3**: Executes trades (paper trading only locally)
- **API**: Serves endpoints that frontend calls
- **SSE**: Broadcasts real-time price updates

### Frontend (Terminal 2)
- **Dashboard**: Shows market data, positions, trades
- **Auto-Trade Toggle**: Controls automated trading
- **Manual Trade Form**: Executes custom trades
- **Tax Log**: Shows trade history
- **API Proxy**: Routes /api/* to localhost:5000

---

## ✅ Success Checklist

- [ ] Python installed & verified
- [ ] Node.js installed & verified
- [ ] Backend dependencies installed (pip install -r requirements.txt)
- [ ] Frontend dependencies installed (npm install)
- [ ] .env file created with API keys
- [ ] Backend running on http://localhost:5000
- [ ] Frontend running on http://127.0.0.1:5173/
- [ ] Dashboard loads in browser
- [ ] Market data shows (SPY, QQQ, VTI)
- [ ] "Refresh All" button works
- [ ] Signals tab shows BUY/SELL
- [ ] Auto-Trade toggle switches
- [ ] Manual trade form submits
- [ ] All 3 tests pass

---

## 🚀 Next Steps

Once running locally:

1. **Explore the dashboard** — Click all tabs, try all features
2. **Test the backend** — Call API endpoints with curl
3. **Run the test suite** — Verify all 23 tests pass
4. **Try a manual trade** — Execute a test trade
5. **Check the logs** — View trade logs & API responses
6. **When ready** → Follow `DEPLOYMENT_GUIDE.md` to go to production

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Start Backend | `cd backend && python server.py` |
| Start Frontend | `cd frontend && npm run dev` |
| Test Data Module | `cd backend && python test_phase5_module1.py` |
| Test Trade Module | `cd backend && python test_phase5_module3.py` |
| Test All APIs | `cd backend && python test_phase5_integration.py` |
| View Backend Logs | `tail -f backend/logs/*.log` |
| Test API | `curl http://localhost:5000/api/market-data` |
| Open Dashboard | `http://127.0.0.1:5173/` |
| Check Market Data | `curl http://localhost:5000/api/market-data` |

---

**Everything is ready to run locally! Follow the Quick Start at top, then enjoy testing Mirai ArcSphere on your machine.** 🎉

---

Created: 2025-03-29  
Status: Ready for Local Development
