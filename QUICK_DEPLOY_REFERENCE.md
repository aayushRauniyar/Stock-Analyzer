# 🚀 QUICK DEPLOYMENT REFERENCE

## 7 Steps to Production (2-4 hours)

### STEP 1: Merge to Main (5 min)
```bash
# https://github.com/aayushRauniyar/Stock-Analyzer/compare/main...copilot-worktree-2026-03-28T23-24-30
# Click "Create pull request" → Fill details → Merge
```

### STEP 2: Backend to Cloud Run (45 min)
```bash
# 1. Setup gcloud
gcloud auth login
gcloud config set project YOUR_GCP_PROJECT

# 2. Enable services
gcloud services enable run.googleapis.com containerregistry.googleapis.com

# 3. Build & deploy
gcloud builds submit --tag gcr.io/YOUR_PROJECT/mirai-backend
gcloud run deploy mirai-backend \
  --image gcr.io/YOUR_PROJECT/mirai-backend \
  --platform managed --region us-central1 --allow-unauthenticated \
  --memory 2Gi --cpu 2

# 4. Save the URL: https://mirai-backend-xxxxx.run.app
```

### STEP 3: Frontend to Vercel (30 min)
```bash
# 1. Install Vercel CLI
npm i -g vercel

# 2. Update env
echo "VITE_API_URL=https://mirai-backend-xxxxx.run.app/api" > frontend/.env.production

# 3. Deploy
cd frontend && vercel --prod

# 4. Save the URL: https://your-project.vercel.app
```

### STEP 4: BigQuery (30 min)
```bash
# 1. Google Cloud Console → BigQuery
# 2. Create Dataset: trading_analytics
# 3. Run SQL from DEPLOYMENT_GUIDE.md (5 tables)
```

### STEP 5: Alpaca API (15 min)
```bash
# 1. Get keys from: https://app.alpaca.markets/paper/dashboard/home
# 2. Set in Cloud Run:
gcloud run services update mirai-backend \
  --set-env-vars \
  APCA_API_KEY_ID=YOUR_KEY,\
  APCA_API_SECRET_KEY=YOUR_SECRET,\
  APCA_API_BASE_URL=https://paper-api.alpaca.markets
```

### STEP 6: Monitoring (15 min)
```bash
# Cloud Console → Logging → Logs Explorer
# View backend logs: resource.type="cloud_run_revision"
```

### STEP 7: Go Live (5 min)
```bash
# Test URLs:
curl https://mirai-backend-xxxxx.run.app/api/market-data
open https://your-project.vercel.app

# Should see dashboard with real data! 🎉
```

---

## Key URLs

| Component | URL | Status |
|-----------|-----|--------|
| Frontend | https://your-project.vercel.app | Live |
| Backend API | https://mirai-backend-xxxxx.run.app | Live |
| GCP Console | https://console.cloud.google.com | Admin |
| BigQuery | Cloud Console → BigQuery | Data |
| Alpaca Dashboard | https://app.alpaca.markets/paper | Paper Trading |

---

## Environment Variables

### Cloud Run (Backend)
```env
APCA_API_KEY_ID=xxx
APCA_API_SECRET_KEY=xxx
APCA_API_BASE_URL=https://paper-api.alpaca.markets
GCP_PROJECT=your-project-id
ENVIRONMENT=production
DEBUG=False
```

### Vercel (Frontend)
```env
VITE_API_URL=https://mirai-backend-xxxxx.run.app/api
```

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Backend not starting | `gcloud run logs read mirai-backend` |
| Frontend can't reach backend | Check VITE_API_URL env var |
| Alpaca auth fails | Verify API keys in Cloud Run env vars |
| BigQuery tables missing | Re-run CREATE TABLE statements |
| High latency | Scale Cloud Run (increase memory/CPU) |

---

## Success Checklist

- [ ] PR merged to main
- [ ] Backend deployed & responding
- [ ] Frontend deployed & loading
- [ ] BigQuery dataset created
- [ ] BigQuery tables created
- [ ] Alpaca keys configured
- [ ] Dashboard shows live data
- [ ] Trades execute successfully

---

## Post-Launch

✅ Monitor Cloud Logs  
✅ Check daily trade success rate  
✅ Review tax log weekly  
✅ Update Alpaca keys monthly  

---

**Total Time: 2-4 hours | Difficulty: Intermediate | Result: Production-Ready Trading Bot 🚀**

See `DEPLOYMENT_GUIDE.md` for detailed instructions with all commands & explanations.
