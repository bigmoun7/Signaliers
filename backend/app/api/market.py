from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from typing import List, Dict, Optional
from ..services.fetcher import fetcher
from ..services.analysis import TechnicalAnalyzer
from ..services.signals import SignalGenerator
from ..services.strategies import Strategies, StrategySignal
from ..services.backtester import Backtester
from ..services.paper_trader import paper_trader
from ..models.schemas import Signal, AnalysisResult, MarketData, BacktestSummary, PaperTradingStatus

router = APIRouter()

@router.post("/paper/start")
async def start_paper_trading(symbol: str, strategy: str, capital: float = 10000000):
    return paper_trader.start(symbol, strategy, capital)

@router.post("/paper/stop")
async def stop_paper_trading():
    return paper_trader.stop()

@router.get("/paper/status", response_model=PaperTradingStatus)
async def get_paper_trading_status():
    return paper_trader.get_status()

@router.get("/strategy/popgun/{symbol}", response_model=List[StrategySignal])
async def get_popgun_strategy(symbol: str, interval: str = "1d", source: str = "YAHOO", period: Optional[str] = None):
    """
    Detects PopGun patterns in historical data.
    """
    try:
        data = await run_in_threadpool(fetcher.get_historical_data, symbol, interval=interval, limit=300, source=source, period=period)
        if not data:
             raise HTTPException(status_code=404, detail=f"Data historis tidak ditemukan untuk {symbol}")
        
        signals = Strategies.detect_popgun(data)
        return signals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/strategy/fvg/{symbol}", response_model=List[StrategySignal])
async def get_fvg_strategy(symbol: str, interval: str = "1d", source: str = "YAHOO", period: Optional[str] = None):
    """
    Detects Bullish Fair Value Gaps (FVG) in historical data.
    """
    try:
        data = await run_in_threadpool(fetcher.get_historical_data, symbol, interval=interval, limit=300, source=source, period=period)
        if not data:
             raise HTTPException(status_code=404, detail=f"Data historis tidak ditemukan untuk {symbol}")
        
        signals = Strategies.detect_fvg(data)
        return signals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/backtest/{strategy}/{symbol}", response_model=BacktestSummary)
async def run_backtest(
    strategy: str, 
    symbol: str, 
    interval: str = "1d", 
    source: str = "YAHOO", 
    period: str = "1y",
    initial_capital: float = 10000000
):
    """
    Runs a backtest for a given strategy and symbol.
    """
    try:
        data = await run_in_threadpool(fetcher.get_historical_data, symbol, interval=interval, limit=1000, source=source, period=period)
        if not data:
             raise HTTPException(status_code=404, detail=f"Data historis tidak ditemukan untuk {symbol}")
        
        # Determine exchange rate
        # If asset is Crypto/US Stock (USD) and capital is IDR (implied by default 10jt)
        # We need to know if the asset is priced in IDR or USD.
        # Simple heuristic: If symbol ends with .JK -> IDR. Else -> USD.
        
        is_idr_asset = symbol.endswith(".JK") or source == "STOCKBIT" or source == "IDX"
        exchange_rate = 1.0 if is_idr_asset else 16000.0 # Default USD rate
        
        backtester = Backtester(data, initial_capital=initial_capital, exchange_rate=exchange_rate)
        result = backtester.run(strategy.upper())
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/signals/{symbol}", response_model=Signal)
async def get_signal(symbol: str, interval: str = "1d"):
    """
    Mengambil data pasar terbaru, melakukan analisis teknikal, dan menghasilkan sinyal.
    """
    try:
        # 1. Ambil Data
        # Dalam produksi, ini akan memanggil API eksternal (Binance/Yahoo)
        raw_data = await run_in_threadpool(fetcher.get_historical_data, symbol, interval=interval, limit=300)
        
        if not raw_data:
            raise HTTPException(status_code=404, detail=f"Data tidak ditemukan untuk {symbol}")

        # 2. Analisis Teknikal
        analyzer = TechnicalAnalyzer(raw_data)
        analysis_result = analyzer.get_latest_analysis(symbol)
        
        if not analysis_result:
            raise HTTPException(status_code=500, detail="Gagal melakukan analisis")

        # 3. Generate Sinyal
        generator = SignalGenerator(analysis_result)
        signal = generator.generate_signal()
        
        return signal

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{symbol}", response_model=List[MarketData])
async def get_history(symbol: str, interval: str = "1d", source: str = "YAHOO", period: Optional[str] = None):
    """
    Mengambil data historis OHLCV untuk charting.
    """
    try:
        # Menggunakan limit 300 agar konsisten dengan analisis
        data = await run_in_threadpool(fetcher.get_historical_data, symbol, interval=interval, limit=300, source=source, period=period)
        if not data:
            raise HTTPException(status_code=404, detail=f"Data historis tidak ditemukan untuk {symbol}")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest/{symbol}", response_model=Optional[MarketData])
async def get_latest(symbol: str, interval: str = "1d", source: str = "YAHOO"):
    """
    Mengambil data candle terakhir untuk update realtime.
    """
    try:
        data = await run_in_threadpool(fetcher.get_latest_candle, symbol, interval=interval, source=source)
        if not data:
            raise HTTPException(status_code=404, detail="Data not available")
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-scan", response_model=List[Signal])
async def scan_market(interval: str = "1d", symbols: Optional[str] = None, source: str = "YAHOO"):
    """
    Melakukan scan pada beberapa simbol populer sekaligus.
    symbols: Comma separated string of symbols.
    """
    if symbols:
        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
    else:
        symbol_list = ["BTC", "ETH", "AAPL", "TSLA", "GOOGL", "GULA", "ISHG"]
    
    results = []
    
    for sym in symbol_list:
        try:
            # Gunakan logika yang sama dengan get_signal
            raw_data = await run_in_threadpool(fetcher.get_historical_data, sym, interval=interval, limit=300, source=source)
            analyzer = TechnicalAnalyzer(raw_data)
            analysis_result = analyzer.get_latest_analysis(sym)
            if analysis_result:
                generator = SignalGenerator(analysis_result)
                results.append(generator.generate_signal())
        except Exception:
            continue
            
    return results