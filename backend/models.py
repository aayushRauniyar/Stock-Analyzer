"""
╔══════════════════════════════════════════════════════════╗
║     MIRAI ARCSPHERE · Trade Record Model                 ║
║     Module 3 — Data Structure for Trades                 ║
╚══════════════════════════════════════════════════════════╝

PURPOSE:
  Represents a single trade record with all metadata needed
  for execution, risk management, and ATO tax compliance.
"""

from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class TradeRecord:
    """
    Represents a complete trade record with entry, exit, and metadata.
    Used for tracking all trades and generating tax logs.
    """
    
    # ─── Trade Identification ─────────────────────
    trade_id: str                    # Unique trade ID (e.g., "trade_2025-03-28_001")
    ticker: str                      # Symbol (SPY, QQQ, VTI)
    
    # ─── Entry Details ─────────────────────────────
    entry_date: datetime             # Date order placed
    entry_price: float               # Entry price (filled price)
    entry_qty: int                   # Number of shares
    entry_side: str                  # "BUY" or "SELL"
    entry_order_id: str              # Alpaca order ID
    
    # ─── Exit Details ──────────────────────────────
    exit_date: Optional[datetime]    # Date order closed (None if open)
    exit_price: Optional[float]      # Exit price (filled price)
    exit_qty: Optional[int]          # Number of shares closed
    exit_side: Optional[str]         # "SELL" (for BUY) or "BUY" (for SELL)
    exit_reason: Optional[str]       # "stop_loss", "take_profit", "manual", "signal_change"
    exit_order_id: Optional[str]     # Alpaca order ID for exit
    
    # ─── AI Analysis Context ───────────────────────
    signal_type: str                 # "BUY", "SELL", "HOLD"
    signal_confidence: int           # 0-100 confidence score
    signal_reasoning: str            # AI explanation for the signal
    analysis_timestamp: datetime     # When the signal was generated
    
    # ─── Risk Management ───────────────────────────
    stop_loss_price: float           # Calculated stop loss (ATR-based)
    take_profit_price: float         # Target exit price
    risk_per_trade_pct: float        # Risk % of account
    max_loss_on_trade: float         # Max loss in $ if stopped out
    
    # ─── Performance ───────────────────────────────
    gross_p_l: Optional[float]       # Profit/loss in $ (entry_value - exit_value)
    net_p_l: Optional[float]         # P&L after commission
    p_l_pct: Optional[float]         # Return % on position
    hold_period_days: Optional[int]  # Days held
    
    # ─── Tax Compliance (ATO) ──────────────────────
    is_short_term: Optional[bool]    # True if held <12 months (ordinary income)
    capital_gains_type: str          # "CGT" or "ordinary_income"
    notes: str                       # Additional context for tax records
    
    def __post_init__(self):
        """Validate trade record on creation."""
        if self.entry_side not in ("BUY", "SELL"):
            raise ValueError(f"Invalid entry_side: {self.entry_side}")
        
        if self.exit_side and self.exit_side not in ("BUY", "SELL"):
            raise ValueError(f"Invalid exit_side: {self.exit_side}")
        
        if not (0 <= self.signal_confidence <= 100):
            raise ValueError(f"Signal confidence must be 0-100, got {self.signal_confidence}")
    
    def to_csv_row(self) -> dict:
        """
        Convert trade to CSV row format for ATO tax log.
        
        Returns:
            Dict with ATO-compliant field names
        """
        return {
            "Date": self.entry_date.strftime("%Y-%m-%d"),
            "Ticker": self.ticker,
            "Side": self.entry_side,
            "Qty": self.entry_qty,
            "Entry Price": f"${self.entry_price:.2f}",
            "Exit Price": f"${self.exit_price:.2f}" if self.exit_price else "OPEN",
            "Entry Date": self.entry_date.strftime("%Y-%m-%d"),
            "Exit Date": self.exit_date.strftime("%Y-%m-%d") if self.exit_date else "OPEN",
            "Hold Days": self.hold_period_days or "N/A",
            "P&L": f"${self.net_p_l:.2f}" if self.net_p_l else "N/A",
            "P&L %": f"{self.p_l_pct:.2f}%" if self.p_l_pct else "N/A",
            "Signal Confidence": f"{self.signal_confidence}%",
            "AI Reasoning": self.signal_reasoning,
            "Exit Reason": self.exit_reason or "OPEN",
            "Capital Gains Type": self.capital_gains_type,
            "Notes": self.notes,
        }
    
    def is_open(self) -> bool:
        """Check if position is still open."""
        return self.exit_date is None
    
    def calculate_hold_period(self) -> int:
        """Calculate days held."""
        end_date = self.exit_date or datetime.now()
        return (end_date.date() - self.entry_date.date()).days
    
    def mark_closed(self, exit_price: float, exit_qty: int, exit_reason: str, exit_order_id: str):
        """
        Mark this trade as closed.
        
        Args:
            exit_price: Price at which position was closed
            exit_qty: Qty closed (may be partial)
            exit_reason: Why it was closed
            exit_order_id: Alpaca order ID for exit
        """
        self.exit_date = datetime.now()
        self.exit_price = exit_price
        self.exit_qty = exit_qty
        self.exit_side = "SELL" if self.entry_side == "BUY" else "BUY"
        self.exit_reason = exit_reason
        self.exit_order_id = exit_order_id
        
        # Calculate P&L
        if self.entry_side == "BUY":
            gross_p_l = (exit_price - self.entry_price) * self.entry_qty
        else:  # SELL
            gross_p_l = (self.entry_price - exit_price) * self.entry_qty
        
        self.gross_p_l = gross_p_l
        self.net_p_l = gross_p_l  # TODO: subtract commission
        
        entry_value = self.entry_price * self.entry_qty
        self.p_l_pct = (self.net_p_l / entry_value * 100) if entry_value > 0 else 0
        
        # Calculate hold period
        self.hold_period_days = self.calculate_hold_period()
        
        # Determine tax type
        self.is_short_term = self.hold_period_days < 365
        self.capital_gains_type = "ordinary_income" if self.is_short_term else "CGT"
