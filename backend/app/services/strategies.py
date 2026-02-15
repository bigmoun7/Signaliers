from typing import List, Dict
from datetime import datetime
from app.models.schemas import MarketData, StrategySignal

class Strategies:
    @staticmethod
    def detect_popgun(data: List[MarketData]) -> List[StrategySignal]:
        signals = []
        if len(data) < 3:
            return signals

        for i in range(2, len(data)):
            mother = data[i-2]
            inside = data[i-1]
            popgun = data[i]

            # Check for Inside Bar (Bar[i-1] inside Bar[i-2])
            is_inside = inside.high <= mother.high and inside.low >= mother.low
            
            if is_inside:
                inside_range = inside.high - inside.low
                popgun_range = popgun.high - popgun.low
                
                # Check for PopGun Bar (Bar[i] bigger than Bar[i-1])
                # And typically breaks out of the inside bar's range
                is_larger = popgun_range > inside_range
                
                # Check if it broke the inside bar's high or low
                broke_high = popgun.high > inside.high
                broke_low = popgun.low < inside.low
                
                if is_larger and (broke_high or broke_low):
                    # Valid PopGun Pattern
                    pg_height = popgun.high - popgun.low
                    
                    # Calculate Targets
                    targets = {
                        "long": {
                            "entry": popgun.high,
                            "tp1": popgun.high + (1.0 * pg_height),
                            "tp2": popgun.high + (2.0 * pg_height),
                            "tp3": popgun.high + (3.0 * pg_height),
                            "sl": popgun.low
                        },
                        "short": {
                            "entry": popgun.low,
                            "tp1": popgun.low - (1.0 * pg_height),
                            "tp2": popgun.low - (2.0 * pg_height),
                            "tp3": popgun.low - (3.0 * pg_height),
                            "sl": popgun.high
                        }
                    }

                    signals.append(StrategySignal(
                        name="PopGun",
                        timestamp=popgun.timestamp,
                        type="NEUTRAL",  # Neutral until breakout confirms direction
                        price=popgun.close,
                        metadata={
                            "mother_idx": i-2,
                            "inside_idx": i-1,
                            "popgun_idx": i,
                            "targets": targets
                        }
                    ))
        
        return signals

    @staticmethod
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
