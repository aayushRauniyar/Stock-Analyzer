"""
╔══════════════════════════════════════════════════════════╗
║     MIRAI ARCSPHERE · Market Context Protocol (MCP)      ║
║     Real-time market data exposure for AI agents         ║
╚══════════════════════════════════════════════════════════╝

PURPOSE:
  Exposes Mirai ArcSphere market data, signals, and positions
  as MCP tools/resources. Allows external AI agents (Claude,
  other LLMs) to query market state without direct API calls.

PROVIDES:
  Resources:
    - market://latest-prices — current market snapshot
    - market://signals — AI signals for all tickers
    - market://positions — open positions and P&L
    - market://risk-status — daily loss, position limits
  
  Tools:
    - query_market_data() — get data for specific ticker
    - query_signals() — check AI signals
    - query_positions() — list open positions
    - check_trading_rules() — verify if trading allowed

DEPENDENCIES:
  pip install mcp
"""

import json
import logging
import sys
import os
from datetime import datetime
from typing import Any

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import MCP SDK
try:
    from mcp.server import Server, Request
    from mcp.types import (
        Resource, Tool, TextContent, ImageContent,
        ResponseStreamOptions
    )
except ImportError:
    print("❌ MCP SDK not installed. Install with: pip install mcp")
    sys.exit(1)

# Import our modules
from module1_market_data import get_market_data, get_all_etf_data, WATCHLIST
from module2_ai_analysis import get_cached_signals, analyse_ticker
from module3_trade_execution import (
    get_account_info, get_open_positions, is_auto_trading_enabled,
    check_daily_loss_limit, get_daily_loss
)
from config import RiskLimits

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("mcp-server")

# ─────────────────────────────────────────────
# MCP SERVER INITIALIZATION
# ─────────────────────────────────────────────

server = Server("mirai-market-data")


# ─────────────────────────────────────────────
# MCP RESOURCES (Read-Only Data)
# ─────────────────────────────────────────────

@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available MCP resources."""
    return [
        Resource(
            uri="market://latest-prices",
            name="Latest Market Prices",
            description="Current prices and technical indicators for SPY, QQQ, VTI",
            mimeType="application/json",
        ),
        Resource(
            uri="market://signals",
            name="AI Trading Signals",
            description="Latest BUY/SELL/HOLD signals from Module 2 AI analysis",
            mimeType="application/json",
        ),
        Resource(
            uri="market://positions",
            name="Open Positions",
            description="Current open positions with entry prices, qty, P&L",
            mimeType="application/json",
        ),
        Resource(
            uri="market://risk-status",
            name="Risk Status",
            description="Daily loss tracking, position limits, trading status",
            mimeType="application/json",
        ),
        Resource(
            uri="market://account",
            name="Account Summary",
            description="Account equity, cash, buying power, portfolio value",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a specific MCP resource."""
    try:
        if uri == "market://latest-prices":
            return json.dumps(get_all_etf_data(), indent=2, default=str)
        
        elif uri == "market://signals":
            signals = get_cached_signals()
            return json.dumps(signals, indent=2, default=str)
        
        elif uri == "market://positions":
            positions = get_open_positions()
            return json.dumps({
                "positions": positions,
                "timestamp": datetime.now().isoformat(),
            }, indent=2, default=str)
        
        elif uri == "market://risk-status":
            can_trade, reason = check_daily_loss_limit()
            return json.dumps({
                "can_trade": can_trade,
                "daily_loss_limit": RiskLimits.DAILY_MAX_LOSS_PCT,
                "daily_loss_realized": get_daily_loss(),
                "auto_trading_enabled": is_auto_trading_enabled(),
                "blocking_reason": reason if not can_trade else None,
                "timestamp": datetime.now().isoformat(),
            }, indent=2, default=str)
        
        elif uri == "market://account":
            account = get_account_info()
            return json.dumps(account, indent=2, default=str)
        
        else:
            return json.dumps({"error": f"Unknown resource: {uri}"})
    
    except Exception as e:
        log.error(f"❌ Failed to read resource {uri}: {e}")
        return json.dumps({"error": str(e)})


# ─────────────────────────────────────────────
# MCP TOOLS (Callable Operations)
# ─────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="query_market_data",
            description="Get current market data for a specific ticker including price, RSI, MACD, Bollinger Bands, and ATR",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Ticker symbol (SPY, QQQ, or VTI)",
                        "enum": WATCHLIST,
                    }
                },
                "required": ["ticker"],
            },
        ),
        Tool(
            name="query_signals",
            description="Get the latest AI trading signals for all watched tickers",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="query_positions",
            description="Get all currently open positions with entry price, quantity, current price, P&L",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="check_trading_rules",
            description="Verify if trading is allowed (check daily loss limit, position limits, auto-trading status)",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="analyze_ticker",
            description="Trigger AI analysis for a specific ticker and get fresh signal",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Ticker symbol to analyze",
                        "enum": WATCHLIST,
                    }
                },
                "required": ["ticker"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute an MCP tool."""
    try:
        if name == "query_market_data":
            ticker = arguments.get("ticker")
            if ticker not in WATCHLIST:
                return [TextContent(type="text", text=f"Error: Invalid ticker {ticker}")]
            
            data = get_market_data(ticker)
            return [TextContent(
                type="text",
                text=json.dumps(data, indent=2, default=str)
            )]
        
        elif name == "query_signals":
            signals = get_cached_signals()
            return [TextContent(
                type="text",
                text=json.dumps(signals, indent=2, default=str)
            )]
        
        elif name == "query_positions":
            positions = get_open_positions()
            return [TextContent(
                type="text",
                text=json.dumps({
                    "positions": positions,
                    "count": len(positions),
                    "timestamp": datetime.now().isoformat(),
                }, indent=2, default=str)
            )]
        
        elif name == "check_trading_rules":
            can_trade, reason = check_daily_loss_limit()
            account = get_account_info()
            positions = get_open_positions()
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "can_trade": can_trade,
                    "daily_loss_blocking_reason": reason if not can_trade else None,
                    "daily_loss_limit_pct": RiskLimits.DAILY_MAX_LOSS_PCT,
                    "daily_loss_realized": get_daily_loss(),
                    "max_position_size_pct": RiskLimits.MAX_POSITION_SIZE_PCT,
                    "max_concurrent_positions": RiskLimits.MAX_CONCURRENT_POSITIONS,
                    "current_positions": len(positions),
                    "auto_trading_enabled": is_auto_trading_enabled(),
                    "account_equity": account.get("equity"),
                    "available_cash": account.get("cash"),
                    "timestamp": datetime.now().isoformat(),
                }, indent=2, default=str)
            )]
        
        elif name == "analyze_ticker":
            ticker = arguments.get("ticker")
            if ticker not in WATCHLIST:
                return [TextContent(type="text", text=f"Error: Invalid ticker {ticker}")]
            
            market_data = get_market_data(ticker)
            signal = analyse_ticker(market_data)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "ticker": ticker,
                    "signal": signal,
                    "analyzed_at": datetime.now().isoformat(),
                }, indent=2, default=str)
            )]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    except Exception as e:
        log.error(f"❌ Tool call failed: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ─────────────────────────────────────────────
# SERVER RUNNER
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 56)
    print("  🌸 MIRAI ARCSPHERE · Market Context Protocol (MCP)")
    print("=" * 56)
    print("  Resources: market:// URIs for data access")
    print("  Tools: Trading operations and analysis")
    print("  Port: stdio (async over stdin/stdout)")
    print("=" * 56)
    
    import asyncio
    asyncio.run(server.run(None, True))
