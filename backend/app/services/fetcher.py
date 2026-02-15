import pandas as pd
import numpy as np
from datetime import datetime, timedelta
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
                 return self._df_to_marketdata(self.cache[cache_key].tail(limit))

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
            self.cache[cache_key] = df
            self.last_fetch[cache_key] = now
            
            return self._df_to_marketdata(df.tail(limit))
            
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

                url = f"https://api.binance.com/api/v3/klines?symbol={binance_symbol}&interval={binance_interval}&limit=1"
                r = requests.get(url, timeout=2)
                if r.status_code == 200:
                    data = r.json()
                    if data and len(data) > 0:
                        kline = data[0]
                        # Binance kline: [Open Time, Open, High, Low, Close, Volume, Close Time, ...]
                        # Timestamp is ms. Use UTC to match Yahoo Finance Crypto (usually UTC)
                        ts = datetime.utcfromtimestamp(kline[0] / 1000)
                        
                        return MarketData(
                            timestamp=ts,
                            open=float(kline[1]),
                            high=float(kline[2]),
                            low=float(kline[3]),
                            close=float(kline[4]),
                            volume=float(kline[5])
                        )
            except Exception as e:
                print(f"Binance fetch failed: {e}")
                pass

        # Fallback to Yahoo Finance (Historical + Fast Info)
        # We use cache for history but we need latest price.
        # Fetching history every second is bad. 
        # Strategy: Get history (cached 60s) + Get Fast Info (Realtime)
        
        # 1. Get Base Candle from History (Cached)
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
                if current_price and current_price > 0:
                    candle.close = current_price
                    # Update High/Low
                    if current_price > candle.high: candle.high = current_price
                    if current_price < candle.low: candle.low = current_price
                    # Note: We keep the timestamp from history to avoid "oldest data" error
        except Exception:
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