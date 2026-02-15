from typing import List, Optional
from datetime import datetime, timezone
import math
from app.models.schemas import MarketData, StrategySignal
from .utils import calculate_atr

def detect_rbd(data: List[MarketData]) -> List[StrategySignal]:
    """
    Replaced with High-Prob SMC: MSS + FVG Retest Strategy.
    Original RBD function name kept for compatibility.
    """
    signals = []
    if len(data) < 25:
        return signals

    # Parameters
    lookback = 20
    atr_mult = 2.0
    use_timer = True
    
    # ATR Calculation
    atr_values = calculate_atr(data, period=14)
    
    # State Variables
    bull_structure = False
    bear_structure = False
    
    bull_fvg_top: Optional[float] = None
    bear_fvg_bot: Optional[float] = None
    
    # Helper for Time Filter (NY Session 07:30 - 12:00)
    # Only apply time filter if data interval is intraday (less than 1 day)
    # Since we don't have interval info here, we can infer from timestamp diffs, 
    # but simplest is to just DISABLE it for now as it causes issues on Weekly/Daily.
    # The user complained about 0% win rate on Weekly.
    
    def is_in_time(ts: datetime):
        # Disable time filter for now to ensure signals on higher timeframes
        return True

    for i in range(lookback, len(data)):
        current = data[i]
        prev = data[i-1]
        
        # 1. Update Structure (MSS)
        # Calculate Highest High / Lowest Low of previous 'lookback' candles (excluding current)
        # Window: [i-lookback, ..., i-1]
        window = data[i-lookback:i]
        high_h = max(c.high for c in window)
        low_l = min(c.low for c in window)
        
        # Check Crossover/Crossunder of CLOSE
        
        # Logic: Break of Structure
        if current.close > high_h:
            bull_structure = True
            bear_structure = False
            
        if current.close < low_l:
            bear_structure = True
            bull_structure = False
            
        # 2. FVG Detection
        # Needs i, i-1, i-2
        c0 = data[i]   # Current
        c1 = data[i-1] # Previous
        c2 = data[i-2] # 2 bars ago
        
        # Bull FVG: Low[0] > High[2] AND Close[1] > High[2] (Valid gap up)
        if c0.low > c2.high and c1.close > c2.high:
            bull_fvg_top = c2.high
            
        # Bear FVG: High[0] < Low[2] AND Close[1] < Low[2] (Valid gap down)
        if c0.high < c2.low and c1.close < c2.low:
            bear_fvg_bot = c2.low
            
        # 3. High Probability Signals (Retest)
        atr = atr_values[i] if i < len(atr_values) else 0
        if atr == 0: continue # Skip if ATR not ready

        # Buy Signal: Bull Structure + Price Retests Bull FVG
        # We want to catch the bounce.
        # Strict Retest: Low touches FVG Top.
        if bull_structure and bull_fvg_top is not None:
             # Check if price dipped into FVG zone (below top) but closed above?
             # Or just simple retest logic: Low < FVG Top
             if current.low <= bull_fvg_top and current.close > bull_fvg_top:
                 # Signal!
                 sl = current.low - (atr * 1.0) # Tighten SL
                 tp = current.close + (atr * 3.0) # Reward 3:1 approx
                 
                 signals.append(StrategySignal(
                    name="SMC Buy",
                    timestamp=current.timestamp,
                    type="BULLISH",
                    price=current.close,
                    metadata={
                        "sl": sl,
                        "tp": tp,
                        "reason": "MSS + FVG Retest",
                        "pivot_type": "DBR" # Legacy compatibility
                    }
                 ))
                 # Reset to avoid spamming signals on same FVG?
                 # Better to keep it active until structure breaks?
                 # For now, consume the FVG to ensure unique signals
                 bull_fvg_top = None

        # Sell Signal: Bear Structure + Price Retests Bear FVG
        if bear_structure and bear_fvg_bot is not None:
            if current.high >= bear_fvg_bot and current.close < bear_fvg_bot:
                # Signal!
                sl = current.high + (atr * 1.0)
                tp = current.close - (atr * 3.0)
                
                signals.append(StrategySignal(
                    name="SMC Sell",
                    timestamp=current.timestamp,
                    type="BEARISH",
                    price=current.close,
                    metadata={
                        "sl": sl,
                        "tp": tp,
                        "reason": "MSS + FVG Retest",
                        "pivot_type": "RBD" # Legacy compatibility
                    }
                ))
                bear_fvg_bot = None

    return signals
