from typing import List, Optional, Tuple
from datetime import datetime
from app.models.schemas import MarketData, StrategySignal
from .utils import calculate_atr

# --- Helper Functions ---

def calculate_sma(data: List[float], period: int) -> List[float]:
    sma_values = []
    for i in range(len(data)):
        if i < period - 1:
            sma_values.append(0.0)
        else:
            window = data[i - period + 1 : i + 1]
            sma_values.append(sum(window) / period)
    return sma_values

def calculate_ema(data: List[float], period: int) -> List[float]:
    ema_values = []
    multiplier = 2 / (period + 1)
    for i, val in enumerate(data):
        if i == 0:
            ema_values.append(val)
        else:
            ema = (val - ema_values[-1]) * multiplier + ema_values[-1]
            ema_values.append(ema)
    return ema_values

def calculate_rsi(data: List[MarketData], period: int = 14) -> List[float]:
    rsi_values = []
    gains = []
    losses = []
    
    for i in range(1, len(data)):
        diff = data[i].close - data[i-1].close
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
        
    avg_gain = sum(gains[:period]) / period if len(gains) >= period else 0
    avg_loss = sum(losses[:period]) / period if len(losses) >= period else 0
    
    # Pad first 'period' values
    rsi_values.extend([0.0] * period)
    
    if avg_loss == 0:
        first_rsi = 100.0
    else:
        rs = avg_gain / avg_loss
        first_rsi = 100.0 - (100.0 / (1.0 + rs))
    rsi_values.append(first_rsi)
    
    for i in range(period, len(gains)):
        gain = gains[i]
        loss = losses[i]
        
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        
        if avg_loss == 0:
            rsi = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100.0 - (100.0 / (1.0 + rs))
        rsi_values.append(rsi)
        
    return rsi_values

def calculate_mfi(data: List[MarketData], period: int = 14) -> List[float]:
    mfi_values = []
    typical_prices = [(d.high + d.low + d.close) / 3.0 for d in data]
    raw_money_flow = [tp * d.volume for tp, d in zip(typical_prices, data)]
    
    positive_flow = []
    negative_flow = []
    
    for i in range(1, len(typical_prices)):
        if typical_prices[i] > typical_prices[i-1]:
            positive_flow.append(raw_money_flow[i])
            negative_flow.append(0.0)
        else:
            positive_flow.append(0.0)
            negative_flow.append(raw_money_flow[i])
            
    # Pad
    mfi_values.extend([0.0] * period)
    
    for i in range(period - 1, len(positive_flow)):
        pos_sum = sum(positive_flow[i-period+1 : i+1])
        neg_sum = sum(negative_flow[i-period+1 : i+1])
        
        if neg_sum == 0:
            mfi = 100.0
        else:
            mr = pos_sum / neg_sum
            mfi = 100.0 - (100.0 / (1.0 + mr))
        mfi_values.append(mfi)
        
    return mfi_values

def calculate_dmi(data: List[MarketData], period: int = 14) -> Tuple[List[float], List[float], List[float]]:
    plus_di = []
    minus_di = []
    adx = []
    
    tr_list = []
    plus_dm_list = []
    minus_dm_list = []
    
    for i in range(1, len(data)):
        curr = data[i]
        prev = data[i-1]
        
        tr = max(curr.high - curr.low, abs(curr.high - prev.close), abs(curr.low - prev.close))
        tr_list.append(tr)
        
        up_move = curr.high - prev.high
        down_move = prev.low - curr.low
        
        if up_move > down_move and up_move > 0:
            plus_dm_list.append(up_move)
        else:
            plus_dm_list.append(0.0)
            
        if down_move > up_move and down_move > 0:
            minus_dm_list.append(down_move)
        else:
            minus_dm_list.append(0.0)
            
    if len(tr_list) < period:
        return [0.0]*len(data), [0.0]*len(data), [0.0]*len(data)
        
    # Smoothed sums (Wilder's)
    # First value is simple sum
    atr_smooth = sum(tr_list[:period])
    plus_dm_smooth = sum(plus_dm_list[:period])
    minus_dm_smooth = sum(minus_dm_list[:period])
    
    # Pad output to match data length
    # data[0] has no prev, so we start at index 1 for calculation
    # but we need to return list of len(data)
    
    # We will build lists that align with `data` indices
    # indices 0..period are 0.0
    plus_di = [0.0] * (period + 1) 
    minus_di = [0.0] * (period + 1)
    
    dx_list = []
    
    # Calculate DI for the rest
    for i in range(period, len(tr_list)):
        atr_smooth = atr_smooth - (atr_smooth / period) + tr_list[i]
        plus_dm_smooth = plus_dm_smooth - (plus_dm_smooth / period) + plus_dm_list[i]
        minus_dm_smooth = minus_dm_smooth - (minus_dm_smooth / period) + minus_dm_list[i]
        
        p_di = 100 * (plus_dm_smooth / atr_smooth) if atr_smooth != 0 else 0
        m_di = 100 * (minus_dm_smooth / atr_smooth) if atr_smooth != 0 else 0
        
        plus_di.append(p_di)
        minus_di.append(m_di)
        
        dx = 100 * abs(p_di - m_di) / (p_di + m_di) if (p_di + m_di) != 0 else 0
        dx_list.append(dx)
        
    # Calculate ADX
    # First ADX is average of first 'period' DX values
    adx = [0.0] * (period + 1 + period - 1) # Padding
    
    if len(dx_list) >= period:
        curr_adx = sum(dx_list[:period]) / period
        adx.append(curr_adx)
        
        for i in range(period, len(dx_list)):
            curr_adx = ((curr_adx * (period - 1)) + dx_list[i]) / period
            adx.append(curr_adx)
            
    # Resize all to len(data)
    plus_di = plus_di[:len(data)] + [0.0]*(len(data)-len(plus_di))
    minus_di = minus_di[:len(data)] + [0.0]*(len(data)-len(minus_di))
    adx = adx[:len(data)] + [0.0]*(len(data)-len(adx))
    
    return plus_di, minus_di, adx

def calculate_cci(data: List[MarketData], period: int = 20) -> List[float]:
    cci_values = []
    tp = [(d.high + d.low + d.close) / 3.0 for d in data]
    
    sma_tp = calculate_sma(tp, period)
    
    for i in range(len(data)):
        if i < period - 1:
            cci_values.append(0.0)
            continue
            
        window_tp = tp[i-period+1 : i+1]
        mean = sma_tp[i]
        md = sum([abs(x - mean) for x in window_tp]) / period
        
        if md == 0:
            cci = 0.0
        else:
            cci = (tp[i] - mean) / (0.015 * md)
        cci_values.append(cci)
        
    return cci_values

# --- Main Strategy ---

def detect_aura(data: List[MarketData]) -> List[StrategySignal]:
    """
    Aura V14 Strategy Implementation (Revised)
    Based on Triple Consensus:
    1. Alpha Trend (MFI-based Trailing Stop)
    2. Magic Trend (CCI-based Momentum)
    3. Lorentzian Score (Proxy using RSI/MFI/ADX Weighted Momentum)
    """
    signals = []
    if len(data) < 50:
        return signals

    # Parameters
    alpha_p = 14
    magic_p = 20
    adx_p = 14
    
    # 1. Indicators
    mfi = calculate_mfi(data, alpha_p)
    atr = calculate_atr(data, alpha_p)
    cci = calculate_cci(data, magic_p)
    _, _, adx = calculate_dmi(data, adx_p)
    rsi = calculate_rsi(data, 14)
    
    # State Vectors
    alpha_trend = [0.0] * len(data)
    alpha_dir = [0] * len(data) # 1 = Bullish, -1 = Bearish
    
    # Track previous signal to avoid duplicates
    last_signal_type = None 
    
    # Loop
    for i in range(1, len(data)):
        # --- A. Alpha Trend Logic ---
        # Logic: If MFI >= 50, use Low-ATR (Bullish Zone). Else High+ATR (Bearish Zone).
        # Then Trail: If Bullish Zone, maintain or increase level. If Bearish Zone, maintain or decrease.
        
        prev_at = alpha_trend[i-1]
        prev_dir = alpha_dir[i-1]
        
        # 1. Determine Zone and Raw Stop
        if mfi[i] >= 50:
            raw_stop = data[i].low - atr[i]
            zone_bull = True
        else:
            raw_stop = data[i].high + atr[i]
            zone_bull = False
            
        # 2. Update Trend and Level
        if i < 20: # Warmup
            alpha_trend[i] = raw_stop
            alpha_dir[i] = 1 if zone_bull else -1
        else:
            if zone_bull:
                if prev_dir == 1:
                    # Already Bullish, Trail Up
                    alpha_trend[i] = max(raw_stop, prev_at)
                    alpha_dir[i] = 1
                else:
                    # Was Bearish, Switch to Bullish if Price > Prev Bear Level?
                    # Or strictly follow MFI zone?
                    # Standard Alpha Trend strictly follows MFI zone for direction switch
                    alpha_trend[i] = raw_stop
                    alpha_dir[i] = 1
            else: # Bearish Zone
                if prev_dir == -1:
                    # Already Bearish, Trail Down
                    alpha_trend[i] = min(raw_stop, prev_at)
                    alpha_dir[i] = -1
                else:
                    # Was Bullish, Switch to Bearish
                    alpha_trend[i] = raw_stop
                    alpha_dir[i] = -1

        # --- B. Magic Trend Logic ---
        # Simple CCI filter
        magic_bull = cci[i] > 0
        magic_bear = cci[i] < 0
        
        # --- C. Lorentzian Score (Momentum Proxy) ---
        # Normalize indicators to -1..1 range approx
        # RSI: (50..100) -> 0..1, (0..50) -> -1..0
        norm_rsi = (rsi[i] - 50) / 50.0
        
        # MFI: Same
        norm_mfi = (mfi[i] - 50) / 50.0
        
        # ADX: Strength multiplier (0..1)
        # Standard trend strength starts at 25.
        # We saturate at 25 to allow moderate trends to contribute fully.
        adx_factor = min(adx[i] / 25.0, 1.0) 
        
        # Composite Score
        # We want Strong Momentum
        score = (norm_rsi + norm_mfi) * adx_factor
        
        # Thresholds
        # Relaxed to 0.05 to allow signals in moderate trends, 
        # relying on Alpha and Magic trends for primary direction.
        # Further relaxed to 0.03 to increase signal frequency as per user feedback
        lorentz_bull = score > 0.03
        lorentz_bear = score < -0.03
        
        # --- D. Triple Consensus ---
        # All three must agree
        
        is_buy = (alpha_dir[i] == 1) and magic_bull and lorentz_bull
        is_sell = (alpha_dir[i] == -1) and magic_bear and lorentz_bear
        
        # --- Re-Entry Logic (Bounce off Alpha Trend Line) ---
        is_reentry_buy = False
        is_reentry_sell = False
        
        if alpha_dir[i] == 1 and magic_bull:
             # If price dipped near Alpha Trend line and closed above
             # Check if Low <= Alpha Trend * 1.005 (0.5% buffer)
             if data[i].low <= alpha_trend[i] * 1.005 and data[i].close > alpha_trend[i]:
                 # Only if we are already in a Bullish state or just confirmed it
                 is_reentry_buy = True

        if alpha_dir[i] == -1 and magic_bear:
             # If price rallied near Alpha Trend line and closed below
             if data[i].high >= alpha_trend[i] * 0.995 and data[i].close < alpha_trend[i]:
                 is_reentry_sell = True

        # --- E. Signal Generation ---
        # Only trigger on CHANGE of consensus state or trend start
        
        current_signal = None
        is_reentry = False
        
        if is_buy:
            current_signal = "BULLISH"
        elif is_sell:
            current_signal = "BEARISH"
        
        # Check Re-entry if no primary signal change
        if not current_signal:
            if is_reentry_buy:
                current_signal = "BULLISH"
                is_reentry = True
            elif is_reentry_sell:
                current_signal = "BEARISH"
                is_reentry = True
            
        # Debounce: Only emit if different from last emitted signal
        # And ensure we don't emit continuously (only on entry)
        
        # Actually, for visualization we might want to know the state.
        # But StrategySignal is an event.
        
        should_emit = False
        if current_signal:
             if current_signal != last_signal_type:
                 should_emit = True
             elif is_reentry:
                 # Re-entry signals can be emitted even if same direction
                 # But we should limit frequency (e.g. not every candle)
                 # For now, let's emit them. Frontend handles clustering?
                 # Or maybe just emit if previous signal was long ago?
                 # Let's emit them.
                 should_emit = True

        if should_emit:
            # New Signal
            signal_name = "Aura V14 Buy" if current_signal == "BULLISH" else "Aura V14 Sell"
            if is_reentry:
                signal_name += " (Re-entry)"
                
            if current_signal == "BULLISH":
                signals.append(StrategySignal(
                    name=signal_name,
                    timestamp=data[i].timestamp,
                    type="BULLISH",
                    price=data[i].close,
                    metadata={
                        "sl": alpha_trend[i], # Use Alpha Trend line as SL
                        "tp": data[i].close + (data[i].close - alpha_trend[i]) * 1.5, # 1.5R
                        "reason": f"Alpha+Magic+Lorentz (Score: {score:.2f})"
                    }
                ))
            else:
                signals.append(StrategySignal(
                    name=signal_name,
                    timestamp=data[i].timestamp,
                    type="BEARISH",
                    price=data[i].close,
                    metadata={
                        "sl": alpha_trend[i],
                        "tp": data[i].close - (alpha_trend[i] - data[i].close) * 1.5,
                        "reason": f"Alpha+Magic+Lorentz (Score: {score:.2f})"
                    }
                ))
            
            # Update last signal type ONLY if it's a primary signal (not re-entry)
            # Or should we update it always?
            # If we have Buy -> Re-entry Buy -> Sell.
            # If we don't update, then Buy -> Re-entry Buy -> Buy (ignored) -> Sell.
            # If we update, Buy -> Re-entry Buy -> Re-entry Buy...
            # We want to avoid spamming Re-entries.
            # So maybe only emit re-entry if `last_signal_type` matches but it's been a while?
            # Let's just update `last_signal_type` so subsequent identical signals are debounced by the `!=` check
            # UNLESS it's a re-entry, which bypasses the check.
            
            if not is_reentry:
                last_signal_type = current_signal
            else:
                # For re-entry, we don't change the "major trend" state.
                # But we might want to prevent back-to-back re-entries?
                # The logic `if current_signal != last_signal_type` handles the major switch.
                # `elif is_reentry` handles the minor ones.
                pass

    return signals
