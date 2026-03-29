# Concerns

## Scalability Risks
- Disk I/O bottleneck `data_snapshots\`. High frequency read/writes between modules for passing huge JSON objects. Could block the server process or create race conditions if multi-threaded requests arrive.
- Single huge `MiraiDashboard.jsx` payload (~1000 lines). The monolithic React structure causes huge re-renders upon state change, notably on interval triggers. As the watchlist or order history scales, browser performance will degrade drastically.

## Technical Debt Stack
- Lack of robust database (e.g., SQLite or Postgres).
- Missing robust WebSocket implementation. Currently pulling data over standard REST polling. Server may be hammered under normal load conditions.

## Known Bugs
- Terminal logging issue regarding `unrealized_pl` inside `module3_trade_execution.py`. An attribute error raised from Alpaca objects lacking field values under dry trading.

## Security 
- Keys (Alpaca/Groq) are loaded via environment variables / stored in `.env`. Must ensure the module logic correctly ignores source keys inside VC.
