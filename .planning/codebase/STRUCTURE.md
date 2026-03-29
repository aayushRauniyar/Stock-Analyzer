# Structure

## Root
`E:\Projects Manu\Stock Analyzer\`
- `DEPLOYMENT_GUIDE.md`: Deployment instructions.
- `README.md`
- `LOCAL_DEV_SETUP.md`: Local startup notes.

## Frontend
`frontend/`
- Vite + React source holding the dashboard user interface (`MiraiDashboard.jsx`).
- Uses inline styling alongside base CSS files (`style` objects mixed with components).
- Single-page interface.

## Backend
`backend/`
- `server.py`: Flask host, port 5000.
- `orchestrator.py`: Controller process holding state schedule.
- `config.py`: Hardcoded constraints (API endpoints, default watchlist path).
- `models.py`: Pydantic / Schema models representing Trades/Watchlist objects.
- `module1_market_data.py`: Technical analysis scripts.
- `module2_ai_analysis.py`: LLM reasoning endpoints via Groq.
- `module3_trade_execution.py`: Order-book API interaction via Alpaca SDK.
- `data_snapshots/`: Directory with persistent json files storing state output between modules.
- `logs/`: Application logging and CSV traces for risk.
