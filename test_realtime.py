
import yfinance as yf
import time

symbol = "BTC-USD"
ticker = yf.Ticker(symbol)

print(f"Testing real-time updates for {symbol}...")
for i in range(5):
    # Method 1: History
    # df = ticker.history(period="1d", interval="1d")
    # price_hist = df['Close'].iloc[-1]
    
    # Method 2: Fast Info
    price_fast = ticker.fast_info['last_price']
    
    print(f"Iter {i+1}: Fast Price = {price_fast}")
    time.sleep(1)
