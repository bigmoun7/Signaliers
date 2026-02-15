from typing import List
from app.models.schemas import MarketData, StrategySignal

def detect_fvg(data: List[MarketData]) -> List[StrategySignal]:
    """
    Detects Bullish Fair Value Gaps (FVG).
    Pattern:
    Bar[i-2]: First candle
    Bar[i-1]: Middle (Impulse) candle (Large body, typically)
    Bar[i]: Third candle
    
    Bullish FVG Condition:
    Low of Bar[i] > High of Bar[i-2]
    The Gap is between High[i-2] and Low[i].
    """
    signals = []
    if len(data) < 3:
        return signals

    for i in range(2, len(data)):
        first = data[i-2]
        middle = data[i-1]
        third = data[i]

        # Bullish FVG
        # 1. Middle candle should be bullish (optional but typical for strong FVG)
        is_bullish_middle = middle.close > middle.open
        
        # 2. Gap Exists
        gap_exists = third.low > first.high
        
        if is_bullish_middle and gap_exists:
            # Valid Bullish FVG
            fvg_top = third.low
            fvg_bottom = first.high
            
            # Check if gap is significant (optional threshold, e.g., > 0.1% price)
            # For now, we take all gaps.
            
            signals.append(StrategySignal(
                name="Bullish FVG",
                timestamp=third.timestamp, # Signal confirmed at close of 3rd candle
                type="BULLISH",
                price=third.close,
                metadata={
                    "fvg_top": fvg_top,
                    "fvg_bottom": fvg_bottom,
                    "mid_price": (fvg_top + fvg_bottom) / 2
                }
            ))
    return signals
