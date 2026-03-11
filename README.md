<p align="center">
  <img src="https://raw.githubusercontent.com/aayushRauniyar/Stock-Analyzer/main/assets/banner.png" alt="Mirai ArcSphere Banner" width="100%">
</p>

# 🌸 Mirai ArcSphere · 未来アークスフィア

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-rose.svg)](https://www.python.org/)
[![Alpaca Markets](https://img.shields.io/badge/Broker-Alpaca_Markets-yellow.svg)](https://alpaca.markets/)
[![Claude AI](https://img.shields.io/badge/AI-Anthropic_Claude-orange.svg)](https://anthropic.com/claude)
[![License: MIT](https://img.shields.io/badge/License-MIT-ink.svg)](https://opensource.org/licenses/MIT)

> **"The future blooms here. · 未来は今ここに咲く"**

Mirai ArcSphere is an open-source **AI-powered ETF trading assistant** built specifically for monitoring `SPY`, `QQQ`, and `VTI`. It utilizes **Anthropic Claude** to generate intelligent technical analysis, executes automated trades via **Alpaca**, and integrates seamlessly with an ATO (Australian Taxation Office) compliant logging system.

---

## ⚡ Features

- **🤖 AI Insights Engine**: Claude analyzes RSI, MACD, and Bollinger Bands to generate actionable BUY/SELL/HOLD signals with detailed reasoning.
- **📈 Auto Trade Execution**: Executes market orders automatically when the AI confidence threshold is met (≥ 70%).
- **🛡️ Risk Management (ASIC Compliant)**: Built-in 3% hard stop-loss and a 5% daily loss limit to protect equity.
- **🧾 ATO Tax Logger**: Instantly logs every executed trade to a CSV file (`tax_trade_log.csv`), making tax preparation simple for July 1.
- **📊 Live Dashboard**: A modern React-based UI to overview your portfolio, open positions, AI insights, and tax logs.
- **🌸 Paper Trading By Default**: Operates using virtual money on real market prices to ensure zero financial risk while testing strategies!

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Broker** | `Alpaca Markets` | Paper & live trading, portfolio data |
| **AI Engine** | `Anthropic Claude` | Market signal generation & risk analysis |
| **Market Data** | `yfinance` | 60-day historical OHLCV data |
| **Indicators** | `ta` (Python) | RSI, MACD, Bollinger Bands, SMA |
| **Dashboard** | `React` + `Tailwind` | Live monitoring |
| **Data processing** | `pandas` + `numpy` | DataFrame manipulation |

---

## 🚀 Quick Start

### 1. Requirements
Ensure you have Python 3.10+ installed and acquire your API keys:
- **Alpaca API Keys (Free)**: [Sign up](https://app.alpaca.markets/)
- **Anthropic API Key**: [Console](https://console.anthropic.com/)

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/aayushRauniyar/Stock-Analyzer.git
cd Stock-Analyzer

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Open `bot.py` and replace the placeholder API keys at the top of the file:
```python
ALPACA_API_KEY    = "YOUR_ALPACA_API_KEY"
ALPACA_SECRET_KEY = "YOUR_ALPACA_SECRET_KEY"
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY"
```

### 4. Launch the Bot 🌸
```bash
python bot.py
```

---

## ⚖️ Legal & Disclaimer

- **For Personal Use Only**: This bot is built for personal algorithmic trading. Operating this for third-party individuals in Australia requires an **ASIC** Australian Financial Services Licence (AFSL).
- **Not Financial Advice**: Mirai ArcSphere is an educational tool. Always begin on a **Paper Trading** account to build confidence in your strategy before investing real capital. 

> *Designed with 🌸 in Adelaide, Australia.*
