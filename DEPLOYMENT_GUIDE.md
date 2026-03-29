# Deployment Guide: Mirai ArcSphere → Production

**Status**: Ready to Deploy  
**Estimated Duration**: 2-4 hours  
**Difficulty**: Intermediate (follow each step carefully)

---

## 📋 Pre-Deployment Checklist

Before you start, ensure you have:

- [x] All code changes committed and pushed
- [x] All 3 test suites passing locally
- [ ] GitHub account with repo access
- [ ] Google Cloud account (for BigQuery)
- [ ] Vercel account (for frontend) or equivalent hosting
- [ ] Alpaca API keys (paper trading account)
- [ ] Basic CLI knowledge (git, Python, npm)

---

## 🎯 Deployment Strategy

```
Local Testing (Phase 5)
    ↓ (if passing)
Merge to Main Branch
    ↓
Deploy Backend (Cloud Run)
    ↓
Deploy Frontend (Vercel)
    ↓
Setup Google Cloud (BigQuery)
    ↓
Configure Alpaca API
    ↓
Go Live 🚀
```

---

## STEP 1: Merge to Main Branch (5 minutes)

### 1.1 Create Pull Request on GitHub

```bash
# Your branch is already pushed
# Go to: https://github.com/aayushRauniyar/Stock-Analyzer/compare/main...copilot-worktree-2026-03-28T23-24-30

# Fill in PR details:
Title: "Phases 1-5: Complete Mirai ArcSphere Rebuild with Testing Suite"

Body: (Copy from PR_TEMPLATE_PHASE4.md in your repo)
```

### 1.2 Merge PR
- [ ] Wait for any automated tests to pass
- [ ] Get approval (if required)
- [ ] Click "Merge pull request"
- [ ] Delete branch after merge

### 1.3 Pull Latest Changes Locally
```bash
cd main-repo-path
git fetch origin
git checkout main
git pull origin main
```

---

## STEP 2: Backend Deployment (Cloud Run) — 45 minutes

### 2.1 Prepare Backend for Production

```bash
# Navigate to backend
cd backend

# Create production config
cat > .env.production << EOF
ENVIRONMENT=production
FLASK_ENV=production
DEBUG=False
LOG_LEVEL=INFO

# Alpaca API (paper trading)
APCA_API_KEY_ID=your_alpaca_key
APCA_API_SECRET_KEY=your_alpaca_secret
APCA_API_BASE_URL=https://paper-api.alpaca.markets

# Google Cloud
GCP_PROJECT=your-gcp-project-id
GCP_CREDENTIALS=path/to/credentials.json

# Flask
FLASK_SECRET_KEY=generate-random-secret-key
MAX_WORKERS=4
EOF
```

### 2.2 Create Docker Setup (Required for Cloud Run)

```bash
# Create Dockerfile in backend/
cat > Dockerfile << EOF
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Run Flask
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "server:app"]
EOF
```

### 2.3 Update requirements.txt (if needed)

```bash
# Add gunicorn for production
echo "gunicorn>=20.1.0" >> requirements.txt
```

### 2.4 Setup Google Cloud Project

```bash
# Install gcloud CLI
# macOS: brew install google-cloud-sdk
# Windows: Download from https://cloud.google.com/sdk/docs/install-sdk

# Login
gcloud auth login
gcloud config set project your-gcp-project-id

# Enable Cloud Run
gcloud services enable run.googleapis.com

# Enable Container Registry
gcloud services enable containerregistry.googleapis.com
```

### 2.5 Build & Deploy Backend

```bash
# Build Docker image
gcloud builds submit --tag gcr.io/your-gcp-project-id/mirai-backend

# Deploy to Cloud Run
gcloud run deploy mirai-backend \
  --image gcr.io/your-gcp-project-id/mirai-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production,DEBUG=False \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600

# Save the URL (you'll need it for frontend)
# It will look like: https://mirai-backend-xxxxx.run.app
```

### 2.6 Verify Backend

```bash
# Test the deployed backend
curl https://mirai-backend-xxxxx.run.app/api/market-data
# Should return JSON with market data
```

---

## STEP 3: Frontend Deployment (Vercel) — 30 minutes

### 3.1 Update API Endpoint

```bash
# In frontend/ directory, update vite.config.js
cat > vite.config.js << EOF
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  }
})
EOF

# Update MiraiDashboard.jsx to use environment variable
# At top of file:
const API_BASE = process.env.VITE_API_URL || 'http://localhost:5000/api'
```

### 3.2 Create .env.production in frontend/

```bash
cd frontend
cat > .env.production << EOF
VITE_API_URL=https://mirai-backend-xxxxx.run.app/api
EOF
```

### 3.3 Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel --prod

# Or use Vercel dashboard:
# 1. Push to GitHub (main branch)
# 2. Go to https://vercel.com/dashboard
# 3. Import your repository
# 4. Set environment variables (VITE_API_URL)
# 5. Deploy
```

### 3.4 Verify Frontend

```bash
# Open the Vercel URL in browser
# Should see: Mirai ArcSphere dashboard loading
# Check: /api/market-data returns data from Cloud Run backend
```

---

## STEP 4: Google Cloud Setup (BigQuery) — 30 minutes

### 4.1 Create BigQuery Dataset

```bash
# Login to Google Cloud Console
# https://console.cloud.google.com

# Navigate to: BigQuery → Create Dataset
# Dataset name: trading_analytics
# Location: US
# Click Create Dataset
```

### 4.2 Create BigQuery Tables

```sql
-- In BigQuery console, run these queries:

-- Table 1: daily_prices
CREATE TABLE `your-gcp-project.trading_analytics.daily_prices` (
  ticker STRING,
  date DATE,
  open FLOAT64,
  high FLOAT64,
  low FLOAT64,
  close FLOAT64,
  volume INT64,
  source STRING,
  fetched_at TIMESTAMP
);

-- Table 2: signals_log
CREATE TABLE `your-gcp-project.trading_analytics.signals_log` (
  timestamp TIMESTAMP,
  ticker STRING,
  signal STRING,
  confidence INT64,
  entry FLOAT64,
  exit FLOAT64,
  stop FLOAT64,
  reason STRING,
  risks ARRAY<STRING>
);

-- Table 3: trade_log
CREATE TABLE `your-gcp-project.trading_analytics.trade_log` (
  timestamp TIMESTAMP,
  ticker STRING,
  action STRING,
  quantity INT64,
  price FLOAT64,
  total FLOAT64,
  reason STRING,
  ai_confidence INT64
);

-- Table 4: positions
CREATE TABLE `your-gcp-project.trading_analytics.positions` (
  ticker STRING,
  quantity INT64,
  entry_price FLOAT64,
  current_price FLOAT64,
  unrealized_pnl FLOAT64,
  last_updated TIMESTAMP
);

-- Table 5: tax_log
CREATE TABLE `your-gcp-project.trading_analytics.tax_log` (
  date DATE,
  ticker STRING,
  action STRING,
  quantity INT64,
  price_per_share FLOAT64,
  total FLOAT64,
  hold_period STRING,
  cost_basis FLOAT64,
  ai_reasoning STRING,
  ai_confidence INT64,
  status STRING
);
```

### 4.3 Setup Stitch MCP Connection

```bash
# In backend/ on your local machine:

# Update stitch_mcp.py with your GCP credentials
export GCP_PROJECT=your-gcp-project-id

# Test connection
python stitch_mcp.py
# Should show: "Starting Mirai Stitch MCP Server..."
```

---

## STEP 5: Configure Alpaca API — 15 minutes

### 5.1 Get Alpaca Credentials

```bash
# Go to: https://app.alpaca.markets/paper/dashboard/home
# Under Settings → API Keys, copy:
#   APCA_API_KEY_ID
#   APCA_API_SECRET_KEY
#   Base URL: https://paper-api.alpaca.markets
```

### 5.2 Set Environment Variables (Cloud Run)

```bash
# Update Cloud Run environment variables
gcloud run services update mirai-backend \
  --set-env-vars \
  APCA_API_KEY_ID=your_key_id,\
  APCA_API_SECRET_KEY=your_secret_key,\
  APCA_API_BASE_URL=https://paper-api.alpaca.markets
```

### 5.3 Test Connection

```bash
# From backend (local), test Alpaca connection
python -c "
import os
from module1_market_data import fetch_alpaca_bars
bars = fetch_alpaca_bars('SPY', days=5)
print(f'✅ Connected! Got {len(bars)} bars')
"
```

---

## STEP 6: Setup Monitoring & Logging — 15 minutes

### 6.1 Enable Cloud Logging

```bash
# Go to Cloud Console → Logging → Logs Explorer
# Filter by resource:
# resource.type="cloud_run_revision"
# resource.labels.service_name="mirai-backend"
```

### 6.2 Create Alerts

```bash
# Cloud Console → Monitoring → Create Alert Policy
# Alert on: 
# - Backend crashes (error rate > 1%)
# - High latency (>2 seconds)
# - Alpaca API failures
```

### 6.3 Setup Logs Sink to BigQuery

```bash
# Cloud Console → Logging → Logs Router
# Create sink to send logs to BigQuery for analysis
```

---

## STEP 7: Go Live! 🚀

### 7.1 Final Health Check

```bash
# 1. Test Frontend
# Open: https://your-vercel-url.vercel.app
# Should see dashboard

# 2. Test Backend
# curl https://mirai-backend-xxxxx.run.app/api/market-data
# Should return JSON

# 3. Test Auto-Trading Toggle
# Click Auto-Trade tab → Toggle ON/OFF
# Should work smoothly

# 4. Test Manual Trade
# Fill trade form → Click Execute
# Should appear in history

# 5. Check Logs
# Cloud Console → Logging → check for errors
```

### 7.2 Enable Real Trading (When Ready)

```bash
# Switch from paper trading to live (CAREFUL!)
# In backend environment variables, change:
# APCA_API_BASE_URL=https://api.alpaca.markets (remove "paper-")
# 
# This will trade with REAL MONEY
# Only do this after extensive testing!
```

---

## 📊 Architecture (After Deployment)

```
┌─────────────────────────────────────────────┐
│         Vercel (Frontend)                   │
│  https://your-project.vercel.app            │
│  ├─ React Dashboard (MiraiDashboard.jsx)    │
│  └─ Static assets (optimized)               │
└────────────┬────────────────────────────────┘
             │ HTTPS REST API + SSE
┌────────────▼────────────────────────────────┐
│    Google Cloud Run (Backend)                │
│  https://mirai-backend-xxxxx.run.app         │
│  ├─ Flask API Server (server.py)             │
│  ├─ Module 1: Market Data                    │
│  ├─ Module 2: AI Analysis                    │
│  ├─ Module 3: Trade Execution                │
│  └─ Stitch MCP Server                        │
└────────────┬────────────────────────────────┘
      ┌──────┼──────┬──────────┐
      ▼      ▼      ▼          ▼
   Alpaca yfinance BigQuery CloudLogs
   API   (fallback) Analytics Monitor
```

---

## ⚙️ Configuration Reference

### Environment Variables Needed

```env
# Backend (.env or Cloud Run)
ENVIRONMENT=production
FLASK_ENV=production
DEBUG=False

# Alpaca API
APCA_API_KEY_ID=your_alpaca_key
APCA_API_SECRET_KEY=your_alpaca_secret
APCA_API_BASE_URL=https://paper-api.alpaca.markets

# Google Cloud
GCP_PROJECT=your-gcp-project-id

# Flask
FLASK_SECRET_KEY=random-generated-key
MAX_WORKERS=4
```

### Frontend Environment Variables

```env
# frontend/.env.production
VITE_API_URL=https://mirai-backend-xxxxx.run.app/api
```

---

## 🔧 Troubleshooting Deployment

| Issue | Solution |
|-------|----------|
| Backend won't start | Check Cloud Run logs: `gcloud run logs read mirai-backend` |
| Frontend can't reach backend | Verify VITE_API_URL in .env.production |
| Alpaca API errors | Verify API keys in Cloud Run environment |
| BigQuery tables missing | Re-run CREATE TABLE statements |
| Database connection errors | Check GCP_PROJECT and credentials |

---

## 📈 Post-Deployment Monitoring

### Daily Checks
- [ ] Dashboard loads without errors
- [ ] Market data updates in real-time
- [ ] Auto-trade toggle works
- [ ] No error spikes in logs

### Weekly Checks
- [ ] Review trading performance in BigQuery
- [ ] Check tax log for completeness
- [ ] Monitor API response times
- [ ] Review Alpaca account balance

### Monthly Checks
- [ ] Performance analysis
- [ ] Cost optimization (Cloud Run, BigQuery)
- [ ] Security review
- [ ] Backup verification

---

## 🚨 Production Runbook

### If Backend Crashes
```bash
# Check logs
gcloud run logs read mirai-backend --limit 50

# Redeploy
gcloud run deploy mirai-backend \
  --image gcr.io/your-gcp-project-id/mirai-backend \
  --platform managed \
  --region us-central1
```

### If Frontend Has Issues
```bash
# Rollback on Vercel
# Dashboard → Deployments → Click "Rollback"

# Or redeploy
cd frontend && vercel --prod
```

### If Trades Stop Executing
```bash
# Check Alpaca API status
curl https://api.alpaca.markets/v1/account

# Check Cloud Run logs for trade errors
gcloud run logs read mirai-backend --limit 100 | grep -i trade
```

---

## 📞 Support Contacts

- **Alpaca API Issues**: https://forum.alpaca.markets
- **Google Cloud Support**: Cloud Console → Support
- **Vercel Issues**: https://vercel.com/support
- **Code Issues**: Check logs and review code

---

## ✅ Deployment Checklist

- [ ] All tests passing locally (Phase 5)
- [ ] PR merged to main branch
- [ ] Backend Docker image built
- [ ] Backend deployed to Cloud Run
- [ ] Frontend deployed to Vercel
- [ ] BigQuery dataset created
- [ ] BigQuery tables created
- [ ] Alpaca API keys configured
- [ ] Environment variables set
- [ ] Health checks passing
- [ ] Monitoring setup complete
- [ ] Team notified
- [ ] Go-live date scheduled

---

## 🎯 Success Indicators (Post-Launch)

✅ Dashboard loads in <2 seconds  
✅ Real-time price updates flowing  
✅ Auto-trade toggle functioning  
✅ Manual trades executing successfully  
✅ Tax log recording all transactions  
✅ No error spikes in logs  
✅ BigQuery receiving data  
✅ 99.9% uptime

---

**Deployment Guide Complete!**

Follow each step sequentially. If you encounter issues, check the troubleshooting section or review the code guides in your repo.

**Estimated total deployment time: 2-4 hours**

Next: Start with STEP 1 (Merge to Main) and work through to STEP 7 (Go Live)! 🚀

---

Created: 2025-03-29  
Status: Ready to Deploy
