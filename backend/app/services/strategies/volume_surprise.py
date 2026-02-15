from typing import List, Dict, Optional, Any
from collections import defaultdict
from datetime import datetime
from ...models.schemas import MarketData, StrategySignal

def analyze_volume_surprise(data: List[MarketData], lookback_periods: int = 20) -> List[Dict[str, Any]]:
    """
    Analyzes volume data and calculates expected volume based on time-based grouping.
    Returns a list of dictionaries containing analysis for each candle.
    """
    results = []
    if not data:
        return results

    # Group volumes by "Period Key"
    # Key strategy: Group by (Weekday, Hour, Minute) to capture time-of-day seasonality.
    volume_history = defaultdict(list)
    
    for i in range(len(data)):
        current = data[i]
        key = f"{current.timestamp.weekday()}-{current.timestamp.hour}-{current.timestamp.minute}"
        history = volume_history[key]

        # Calculate expected volume
        expected_volume = 0.0
        if len(history) >= 3:
            # Use average of last N matching periods
            relevant_history = history[-lookback_periods:]
            expected_volume = sum(relevant_history) / len(relevant_history)
        else:
            # Not enough history for this specific time slot.
            # Fallback: Use simple moving average of last 20 periods regardless of time
            if i >= 20:
                prev_vols = [d.volume for d in data[i-20:i]]
                expected_volume = sum(prev_vols) / 20
            else:
                expected_volume = current.volume # No history, no surprise possible

        results.append({
            "timestamp": current.timestamp,
            "volume": current.volume,
            "expected_volume": expected_volume,
            "close": current.close,
            "open": current.open,
            "high": current.high,
            "low": current.low,
            "is_bullish": current.close > current.open
        })

        # Update volume history for this key
        volume_history[key].append(current.volume)
    
    return results

def detect_volume_surprise(data: List[MarketData]) -> List[StrategySignal]:
    """
    Volume Surprise Strategy based on LuxAlgo logic.
    Detects when current volume significantly exceeds the expected volume for that specific time/day.
    """
    signals = []
    if len(data) < 50:
        return signals

    # Configuration
    lookback_periods = 20 
    surprise_threshold = 1.5 # Lowered from 2.0 to 1.5 to catch more significant volume events
    min_volume = 1000 # Minimum volume filter to avoid low liquidity noise

    analysis_results = analyze_volume_surprise(data, lookback_periods)

    for i, res in enumerate(analysis_results):
        current_volume = res["volume"]
        expected_volume = res["expected_volume"]
        
        # Check for surprise
        if expected_volume > 0:
            is_surprise = current_volume > (expected_volume * surprise_threshold)
            
            if is_surprise and current_volume > min_volume:
                # Determine signal type based on price action
                range_len = res["high"] - res["low"]
                
                if res["is_bullish"]:
                    signal_type = "BULLISH"
                    reason = f"Bullish Volume Surprise (Vol: {current_volume:.0f}, Exp: {expected_volume:.0f}, x{current_volume/expected_volume:.1f})"
                    
                    # SL/TP Logic
                    sl = res["low"] - range_len * 0.5 
                    tp = res["close"] + range_len * 2.0
                    
                    signals.append(StrategySignal(
                        name="Volume Surprise Buy",
                        timestamp=res["timestamp"],
                        type="BULLISH",
                        price=res["close"],
                        metadata={
                            "sl": sl,
                            "tp": tp,
                            "reason": reason,
                            "volume_ratio": round(current_volume/expected_volume, 2)
                        }
                    ))
                
                else:
                    signal_type = "BEARISH"
                    reason = f"Bearish Volume Surprise (Vol: {current_volume:.0f}, Exp: {expected_volume:.0f}, x{current_volume/expected_volume:.1f})"
                    
                    # SL/TP Logic
                    sl = res["high"] + range_len * 0.5
                    tp = res["close"] - range_len * 2.0
                    
                    signals.append(StrategySignal(
                        name="Volume Surprise Sell",
                        timestamp=res["timestamp"],
                        type="BEARISH",
                        price=res["close"],
                        metadata={
                            "sl": sl,
                            "tp": tp,
                            "reason": reason,
                            "volume_ratio": round(current_volume/expected_volume, 2)
                        }
                    ))

    return signals
