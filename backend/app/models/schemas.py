from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class MarketData(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class AnalysisResult(BaseModel):
    symbol: str
    price: float
    volume: float
    rsi: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    upper_band: Optional[float] = None
    lower_band: Optional[float] = None
    volume_avg: Optional[float] = None
    timestamp: datetime

class Signal(BaseModel):
    symbol: str
    price: float
    signal_type: str  # BUY, SELL, WATCH
    reasons: List[str]
    timestamp: datetime

class StrategySignal(BaseModel):
    name: str
    timestamp: datetime
    type: str  # "BULLISH", "BEARISH", "NEUTRAL"
    price: float
    metadata: dict = {}  # Store targets, stop loss, etc.

class TradeResult(BaseModel):
    entry_date: datetime
    exit_date: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    position: str # "LONG" or "SHORT"
    status: str # "WIN", "LOSS", "OPEN"
    pnl: float # In Quote Currency (e.g. USD)
    pnl_percent: float
    invested: float # In Base Currency (e.g. IDR if converted)
    realized_value: float # Final value
    
class BacktestSummary(BaseModel):
    strategy: str
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    total_pnl: float
    trades: List[TradeResult]

class PaperTrade(BaseModel):
    id: str
    symbol: str
    strategy: str
    entry_date: datetime
    entry_price: float
    quantity: float
    initial_capital: float
    current_price: float
    pnl: float
    pnl_percent: float
    status: str # OPEN, CLOSED
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    
class PaperTradingStatus(BaseModel):
    is_active: bool
    active_symbol: Optional[str] = None
    active_strategy: Optional[str] = None
    trades: List[PaperTrade]
    balance: float