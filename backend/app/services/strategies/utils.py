from typing import List
from app.models.schemas import MarketData

def calculate_atr(data: List[MarketData], period: int = 14) -> List[float]:
    tr_list = []
    for i in range(len(data)):
        if i == 0:
            tr = data[i].high - data[i].low
        else:
            prev_close = data[i-1].close
            tr = max(data[i].high - data[i].low, 
                     abs(data[i].high - prev_close), 
                     abs(data[i].low - prev_close))
        tr_list.append(tr)
    
    atr_list = []
    # Simple SMA of TR for ATR
    # First ATR is average of first period TRs
    current_atr = sum(tr_list[:period]) / period if len(tr_list) >= period else 0
    atr_list.extend([0] * (period - 1)) # Pad beginning
    atr_list.append(current_atr)
    
    for i in range(period, len(tr_list)):
        current_atr = ((current_atr * (period - 1)) + tr_list[i]) / period
        atr_list.append(current_atr)
        
    return atr_list
