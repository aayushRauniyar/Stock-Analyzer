# Integrations

## Market Data
- **Yahoo Finance API** (via `yfinance`): Pulls real-time tick data and historic candles (`backend/module1_market_data.py`).

## Trade Execution & Account Management
- **Alpaca API** (via `alpaca-trade-api`): Executes Smart Orders and handles paper trading portfolio (`backend/module3_trade_execution.py`).
- **Keys**: `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`

## AI Inference
- **Groq API** (via `groq`): Generates LLM analysis derived from scraped data and indicators. Used in `backend/module2_ai_analysis.py`.
- **Keys**: `GROQ_API_KEY`

## Meta Protocol
- **Model Context Protocol (MCP)**: Server configured via `backend/mcp_server.py`.
