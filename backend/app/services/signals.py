from ..models.schemas import AnalysisResult, Signal

class SignalGenerator:
    def __init__(self, analysis: AnalysisResult):
        self.analysis = analysis

    def generate_signal(self) -> Signal:
        # Simple mock logic
        signal_type = "WATCH"
        reasons = []
        
        if self.analysis.rsi and self.analysis.rsi < 30:
            signal_type = "BUY"
            reasons.append("RSI Oversold (< 30)")
        elif self.analysis.rsi and self.analysis.rsi > 70:
            signal_type = "SELL"
            reasons.append("RSI Overbought (> 70)")
            
        return Signal(
            symbol=self.analysis.symbol,
            price=self.analysis.price,
            signal_type=signal_type,
            reasons=reasons,
            timestamp=self.analysis.timestamp
        )