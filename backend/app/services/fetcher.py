import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
import yfinance as yf
import requests
from ..models.schemas import MarketData

class DataFetcher:
    """
    Kelas untuk mengambil data pasar real dari Yahoo Finance.
    """
    
    def __init__(self):
        # Cache sederhana di memory: key = symbol_interval
        self.cache: Dict[str, pd.DataFrame] = {}
        self.last_fetch: Dict[str, datetime] = {}

    def _map_symbol(self, symbol: str, source: str = "YAHOO") -> str:
        """
        Mapping simbol dari input user ke format Yahoo Finance.
        """
        symbol = symbol.upper().strip()
        
        # Jika user sudah menyertakan suffix yang benar, kembalikan
        if symbol.endswith(".JK") or symbol.endswith("-USD"):
            return symbol

        # Mapping khusus berdasarkan Source
        if source in ["BINANCE", "COINGECKO"]:
            # Asumsi Crypto -> tambahkan -USD jika belum ada
            return f"{symbol}-USD"
            
        if source in ["STOCKBIT", "IDX"]:
             # Asumsi Saham Indonesia -> tambahkan .JK
             return f"{symbol}.JK"

        # Default / YAHOO Logic
        if symbol == "ISHG" or symbol == "IHSG":
            return "^JKSE"
        
        # Crypto populer
        crypto_list = ["BTC", "ETH", "WIF", "SOL", "BNB", "XRP", "DOGE", "SHIB", "PEPE"]
        if symbol in crypto_list:
            return f"{symbol}-USD"
            
        # Saham Indo populer
        known_indo_stocks = ["GULA", "BBCA", "BBRI", "BMRI", "TLKM", "ASII", "UNVR", "GOTO", "BBNI", "ADRO"]
        if symbol in known_indo_stocks:
            return f"{symbol}.JK"
            
        # Fallback logic
        # Jika 4 huruf, coba .JK kecuali ticker US populer
        if len(symbol) == 4 and symbol.isalpha():
             us_tech = ["AAPL", "MSFT", "META", "AMZN", "TSLA", "GOOG", "NFLX", "NVDA"]
             if symbol in us_tech:
                 return symbol
             return f"{symbol}.JK"
            
        return symbol

    def _get_period_for_interval(self, interval: str) -> str:
        """
        Menentukan periode fetch berdasarkan interval.
        """
        interval = interval.lower()
        if interval in ["1m"]:
            return "1d" # Max 7d
        if interval in ["5m", "15m", "30m"]:
            return "5d" # Max 60d
        if interval in ["1h", "60m"]:
            return "1mo" # Max 730d
        if interval in ["1d"]:
            return "1y"
        if interval in ["1wk"]:
            return "2y"
        if interval in ["1mo"]:
            return "5y"
        return "1y" # Default

    def get_historical_data(self, symbol: str, interval: str = "1d", limit: int = 300, source: str = "YAHOO", use_cache: bool = True, period: str = None) -> List[MarketData]:
        yf_symbol = self._map_symbol(symbol, source)
        cache_key = f"{yf_symbol}_{interval}_{period}"
        
        # Cek cache (valid selama 1 menit)
        now = datetime.now()
        if use_cache and cache_key in self.cache and cache_key in self.last_fetch:
            if (now - self.last_fetch[cache_key]).total_seconds() < 60:
                 # Return cached data (converted to list)
                 data = self._df_to_marketdata(self.cache[cache_key].tail(limit))
                 # Ensure timezone aware
                 for d in data:
                     if d.timestamp.tzinfo is None:
                         d.timestamp = d.timestamp.replace(tzinfo=timezone.utc)
                 return data

        try:
            if not period:
                period = self._get_period_for_interval(interval)
            
            ticker = yf.Ticker(yf_symbol)
            # Fetch data
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                 # Fallback logic could be added here
                 return []

            # Update cache
            # Remove duplicates based on index (Date/Datetime)
            df = df[~df.index.duplicated(keep='last')]
            
            self.cache[cache_key] = df
            self.last_fetch[cache_key] = now
            
            data = self._df_to_marketdata(df.tail(limit))
            # Ensure timezone aware
            for d in data:
                if d.timestamp.tzinfo is None:
                    d.timestamp = d.timestamp.replace(tzinfo=timezone.utc)
            return data
            
        except Exception as e:
            print(f"Error fetching {yf_symbol} ({interval}): {e}")
            return []

    def get_latest_candle(self, symbol: str, interval: str = "1d", source: str = "YAHOO") -> Optional[MarketData]:
        # Try Binance for Crypto first (Faster & Reliable)
        yf_symbol = self._map_symbol(symbol, source)
        is_crypto = "-USD" in yf_symbol or source in ["BINANCE", "COINGECKO"]
        
        if is_crypto:
            try:
                # Map interval to Binance format
                # Binance: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
                binance_interval = interval
                if interval == "1wk": binance_interval = "1w"
                if interval == "1mo": binance_interval = "1M"
                
                binance_symbol = yf_symbol.replace("-USD", "USDT").replace("-", "").upper()
                if not binance_symbol.endswith("USDT"):
                     binance_symbol += "USDT"

                # Fetch Kline (for Open, High, Low of the period)
                url_kline = f"https://api.binance.com/api/v3/klines?symbol={binance_symbol}&interval={binance_interval}&limit=1"
                # Fetch Ticker Price (for absolute latest Close)
                url_price = f"https://api.binance.com/api/v3/ticker/price?symbol={binance_symbol}"
                
                print(f"DEBUG: Fetching Binance {url_kline}")
                r_kline = requests.get(url_kline, timeout=2)
                r_price = requests.get(url_price, timeout=2)
                
                if r_kline.status_code == 200 and r_price.status_code == 200:
                    data = r_kline.json()
                    price_data = r_price.json()
                    
                    if data and len(data) > 0 and 'price' in price_data:
                        kline = data[0]
                        current_price = float(price_data['price'])
                        
                        # Binance kline: [Open Time, Open, High, Low, Close, Volume, Close Time, ...]
                        # Timestamp is ms. Use UTC to match Yahoo Finance Crypto (usually UTC)
                        ts = datetime.fromtimestamp(kline[0] / 1000, tz=timezone.utc)
                        
                        candle = MarketData(
                            timestamp=ts,
                            open=float(kline[1]),
                            high=float(kline[2]),
                            low=float(kline[3]),
                            close=current_price, # Use ticker price for latest close
                            volume=float(kline[5])
                        )
                        
                        # Adjust High/Low with latest price
                        if current_price > candle.high: candle.high = current_price
                        if current_price < candle.low: candle.low = current_price
                        
                        print(f"DEBUG: Binance Success {symbol} {candle.close}")
                        return candle
            except Exception as e:
                print(f"Binance fetch failed: {e}")
                pass

        # Fallback to Yahoo Finance (Historical + Fast Info)
        # We use cache for history but we need latest price.
        # Fetching history every second is bad. 
        # Strategy: Get history (cached 60s) + Get Fast Info (Realtime)
        
        # 1. Get Base Candle from History (Cached)
        # If we rely solely on cache, we might get stale data if fast_info fails.
        # But for 'latest', maybe we should try to refresh if cache is old?
        # For now keep use_cache=True to avoid rate limits.
        base_data = self.get_historical_data(symbol, interval=interval, limit=1, source=source, use_cache=True)
        if not base_data:
            return None
            
        candle = base_data[-1]
        
        # 2. Update with Realtime Price if available (Fast Info)
        try:
             ticker = yf.Ticker(yf_symbol)
             # fast_info access is usually faster than history()
             if hasattr(ticker, 'fast_info') and 'last_price' in ticker.fast_info:
                current_price = ticker.fast_info['last_price']
                
                # Check for new day (Daily candle only)
                is_new_day = False
                if interval == '1d':
                     last_date = candle.timestamp.date()
                     today_date = datetime.now().date()
                     if last_date < today_date:
                         is_new_day = True

                if is_new_day:
                    # Create new candle for today
                    print(f"DEBUG: Creating new daily candle for {symbol}")
                    new_candle = MarketData(
                        timestamp=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0),
                        open=ticker.fast_info.get('open', current_price),
                        high=ticker.fast_info.get('day_high', current_price),
                        low=ticker.fast_info.get('day_low', current_price),
                        close=current_price,
                        volume=ticker.fast_info.get('last_volume', 0)
                    )
                    return new_candle

                if current_price and current_price > 0:
                    print(f"DEBUG: Yahoo FastInfo {symbol} Old:{candle.close} New:{current_price}")
                    candle.close = current_price
                    # Update High/Low
                    if current_price > candle.high: candle.high = current_price
                    if current_price < candle.low: candle.low = current_price
                    # Note: We keep the timestamp from history to avoid "oldest data" error
                    # Make sure timestamp is timezone-aware UTC
                    if candle.timestamp.tzinfo is None:
                        candle.timestamp = candle.timestamp.replace(tzinfo=timezone.utc)
        except Exception as e:
            # print(f"DEBUG: Yahoo FastInfo Failed {e}")
            pass
            
        return candle

    def _df_to_marketdata(self, df: pd.DataFrame) -> List[MarketData]:
        results = []
        # Reset index to get Date/Datetime column
        df = df.reset_index()
        
        for _, row in df.iterrows():
            # YFinance date column name varies ('Date' or 'Datetime')
            ts = row.get('Datetime') or row.get('Date')
            
            # Ensure timestamp is datetime object
            if isinstance(ts, pd.Timestamp):
                ts = ts.to_pydatetime()
            
            # YF sometimes has timezone info, we might want to normalize or keep it
            # Pydantic handles datetime, but frontend expects ISO string usually
            
            results.append(MarketData(
                timestamp=ts,
                open=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                volume=row['Volume']
            ))
        return results

# Singleton instance
fetcher = DataFetcher()