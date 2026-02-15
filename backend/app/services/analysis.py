from typing import List, Optional
from ..models.schemas import MarketData, AnalysisResult

class TechnicalAnalyzer:
    def __init__(self, data: List[MarketData]):
        self.data = data

    def get_latest_analysis(self, symbol: str) -> Optional[AnalysisResult]:
        if not self.data:
            return None
            
        last_candle = self.data[-1]
        
        # Simple Logic without pandas_ta for now (to avoid dependency issues)
        # We can implement basic SMA/RSI calculation manually here if needed
        # For now, we return basic price info to ensure dashboard works
        
        prices = [d.close for d in self.data]
        
        # Calculate Simple SMA 50
        sma_50 = None
        if len(prices) >= 50:
            sma_50 = sum(prices[-50:]) / 50
            
        # Calculate RSI (Simplified 14 periods)
        rsi = 50.0
        if len(prices) > 14:
            deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
            gains = [d for d in deltas if d > 0]
            losses = [abs(d) for d in deltas if d < 0]
            
            avg_gain = sum(gains[-14:]) / 14 if gains else 0
            avg_loss = sum(losses[-14:]) / 14 if losses else 0
            
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

        return AnalysisResult(
            symbol=symbol,
            price=last_candle.close,
            volume=last_candle.volume,
            rsi=rsi,
            sma_50=sma_50,
            sma_200=None, # Need more data
            macd=None,
            macd_signal=None,
            upper_band=None,
            lower_band=None,
            volume_avg=None,
            timestamp=last_candle.timestamp
        )