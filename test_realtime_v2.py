
import yfinance as yf
import time
import datetime

symbol = "BTC-USD"
print(f"Testing real-time updates for {symbol}...")

for i in range(5):
    # Re-create ticker to ensure fresh data
    ticker = yf.Ticker(symbol)
    
    # Method 1: History (Standard)
    try:
        df = ticker.history(period="1d", interval="1d")
        if not df.empty:
            price_hist = df['Close'].iloc[-1]
            time_hist = df.index[-1]
        else:
            price_hist = "N/A"
            time_hist = "N/A"
    except Exception as e:
        price_hist = f"Error: {e}"

    # Method 2: Fast Info (Real-time snapshot)
    try:
        price_fast = ticker.fast_info['last_price']
    except Exception as e:
        price_fast = f"Error: {e}"
    
    print(f"Iter {i+1} [{datetime.datetime.now().time()}]: History={price_hist} | FastInfo={price_fast}")
    time.sleep(1)
