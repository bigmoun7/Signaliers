import React, { useState, useEffect } from 'react';
import Chart from './Chart';

const Dashboard = () => {
  const [signals, setSignals] = useState([]);
  const [selectedSymbol, setSelectedSymbol] = useState("BTC");
  const [selectedInterval, setSelectedInterval] = useState("1d");
  const [assetType, setAssetType] = useState("CRYPTO"); // CRYPTO, STOCK
  const [marketSource, setMarketSource] = useState("YAHOO"); // YAHOO, BINANCE, COINGECKO, STOCKBIT
  const [selectedStrategy, setSelectedStrategy] = useState("NONE"); // NONE, POPGUN
  const [selectedPeriod, setSelectedPeriod] = useState("1y");

  const STRATEGIES = [
    { id: 'NONE', label: 'No Strategy' },
    { id: 'POPGUN', label: 'PopGun Pattern' },
    { id: 'FVG', label: 'Smart Money Concept (FVG)' }
  ];

  const PERIOD_OPTIONS = [
    { value: '1d', label: '1 Day' },
    { value: '5d', label: '5 Days' },
    { value: '1mo', label: '1 Month' },
    { value: '3mo', label: '3 Months' },
    { value: '6mo', label: '6 Months' },
    { value: '1y', label: '1 Year' },
    { value: '2y', label: '2 Years' },
    { value: '5y', label: '5 Years' },
    { value: 'ytd', label: 'YTD' },
    { value: 'max', label: 'Max' },
  ];
  
  const WATCHLIST_OPTIONS = [
    { id: 'lq45', label: 'IDX LQ45 (Saham)', symbols: ['BBCA', 'BBRI', 'TLKM', 'BMRI', 'ASII', 'GOTO', 'UNVR'] },
    { id: 'tech_us', label: 'US Tech (Saham)', symbols: ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA'] },
    { id: 'top_crypto', label: 'Top Crypto', symbols: ['BTC', 'ETH', 'SOL', 'BNB', 'XRP'] },
    { id: 'meme', label: 'Meme Coins', symbols: ['DOGE', 'SHIB', 'PEPE', 'WIF'] },
  ];

  const [selectedWatchlist, setSelectedWatchlist] = useState(['top_crypto']); // Default to Top Crypto

  const [isChartVisible, setIsChartVisible] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Backtest State
  const [backtestResult, setBacktestResult] = useState(null);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [backtestError, setBacktestError] = useState(null);
  const [initialCapital, setInitialCapital] = useState(10000000);

  // Paper Trading State
  const [paperStatus, setPaperStatus] = useState(null);
  const [paperLoading, setPaperLoading] = useState(false);

  // Fetch signals
  const fetchSignals = async () => {
    setLoading(true);
    try {
      // Resolve symbols from watchlist
      let symbolsToScan = [];
      selectedWatchlist.forEach(groupId => {
        const group = WATCHLIST_OPTIONS.find(g => g.id === groupId);
        if (group) {
          symbolsToScan = [...symbolsToScan, ...group.symbols];
        }
      });
      
      // Remove duplicates
      symbolsToScan = [...new Set(symbolsToScan)];
      
      // If empty, use default
      if (symbolsToScan.length === 0) symbolsToScan = ['BTC', 'ETH'];

      const queryParams = new URLSearchParams({
        interval: selectedInterval,
        symbols: symbolsToScan.join(','),
        source: marketSource
      });

      const response = await fetch(`http://127.0.0.1:8000/api/market-scan?${queryParams}`);
      if (!response.ok) throw new Error('Failed to fetch signals');
      const data = await response.json();
      setSignals(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBacktest = async () => {
    if (selectedStrategy === "NONE") {
        setBacktestError("Please select a strategy first.");
        return;
    }

    setBacktestLoading(true);
    setBacktestResult(null);
    setBacktestError(null);

    try {
        const queryParams = new URLSearchParams({
            interval: selectedInterval,
            source: marketSource,
            period: selectedPeriod,
            initial_capital: initialCapital
        });

        const response = await fetch(`http://127.0.0.1:8000/api/backtest/${selectedStrategy}/${selectedSymbol}?${queryParams}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to run backtest');
        }
        
        const data = await response.json();
        setBacktestResult(data);
    } catch (err) {
        setBacktestError(err.message);
    } finally {
        setBacktestLoading(false);
    }
  };

  const fetchPaperStatus = async () => {
      try {
          const response = await fetch('http://127.0.0.1:8000/api/paper/status');
          if (response.ok) {
              const data = await response.json();
              setPaperStatus(data);
          }
      } catch (err) {
          console.error("Failed to fetch paper status", err);
      }
  };

  const handleStartPaper = async () => {
      if (selectedStrategy === "NONE") return;
      setPaperLoading(true);
      try {
          await fetch(`http://127.0.0.1:8000/api/paper/start?symbol=${selectedSymbol}&strategy=${selectedStrategy}&capital=${initialCapital}`, { method: 'POST' });
          fetchPaperStatus();
      } catch (err) {
          console.error(err);
      } finally {
          setPaperLoading(false);
      }
  };

  const handleStopPaper = async () => {
      setPaperLoading(true);
      try {
          await fetch('http://127.0.0.1:8000/api/paper/stop', { method: 'POST' });
          fetchPaperStatus();
      } catch (err) {
          console.error(err);
      } finally {
          setPaperLoading(false);
      }
  };

  useEffect(() => {
    fetchSignals();
    fetchPaperStatus();
    const interval = setInterval(() => {
        fetchSignals();
        fetchPaperStatus();
    }, 1000); // Refresh signals every 1s
    return () => clearInterval(interval);
  }, [selectedWatchlist, marketSource]); // Re-fetch when watchlist or source changes

  const handleSymbolChange = (e) => {
    setSelectedSymbol(e.target.value);
  };

  const handleIntervalChange = (e) => {
    setSelectedInterval(e.target.value);
  };

  const handleSymbolSubmit = (e) => {
    e.preventDefault();
    // Chart will automatically update because selectedSymbol state changes
  };

  return (
    <div className="container mx-auto p-4 space-y-6">
      <header className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-gray-800">Signaliers Dashboard</h1>
        <div className="flex gap-2">
            <button 
                onClick={() => setIsChartVisible(!isChartVisible)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
            >
                {isChartVisible ? "Hide Chart" : "Show Chart"}
            </button>
            <button 
                onClick={fetchSignals}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition"
            >
                Refresh Data
            </button>
        </div>
      </header>

      {/* Chart Section */}
      {isChartVisible && (
        <section className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-xl font-semibold mb-4">Live Market Chart (TradingView Style)</h2>
          
          <div className="flex gap-4 mb-4 flex-wrap">
             {/* Asset Type Dropdown */}
             <div className="flex flex-col">
                <label className="text-xs text-gray-500 mb-1">Tipe Aset</label>
                <select 
                  value={assetType}
                  onChange={(e) => setAssetType(e.target.value)}
                  className="border p-2 rounded w-32"
                >
                  <option value="STOCK">Saham</option>
                  <option value="CRYPTO">Kripto</option>
                </select>
             </div>

             {/* Market Source Dropdown */}
             <div className="flex flex-col">
                <label className="text-xs text-gray-500 mb-1">Data Source</label>
                <select 
                  value={marketSource}
                  onChange={(e) => setMarketSource(e.target.value)}
                  className="border p-2 rounded w-40"
                >
                  <option value="YAHOO">Yahoo Finance</option>
                  <option value="BINANCE">Binance</option>
                  <option value="COINGECKO">Coin Gecko</option>
                  <option value="STOCKBIT">Stockbit</option>
                </select>
             </div>
          </div>

          <form onSubmit={handleSymbolSubmit} className="mb-4 flex gap-2 items-end">
            <div className="flex flex-col">
                <label className="text-xs text-gray-500 mb-1">Simbol</label>
                <input 
                type="text" 
                value={selectedSymbol}
                onChange={handleSymbolChange}
                className="border p-2 rounded w-40 uppercase"
                placeholder="Symbol (e.g. BTC)" 
                />
            </div>
            
            <div className="flex flex-col">
                <label className="text-xs text-gray-500 mb-1">Periode</label>
                <select 
                  value={selectedPeriod}
                  onChange={(e) => setSelectedPeriod(e.target.value)}
                  className="border p-2 rounded w-32"
                >
                  {PERIOD_OPTIONS.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
            </div>

            <div className="flex flex-col">
                <label className="text-xs text-gray-500 mb-1">Interval</label>
                <select 
                value={selectedInterval}
                onChange={handleIntervalChange}
                className="border p-2 rounded w-32"
                >
                <option value="1m">1 Menit</option>
                <option value="5m">5 Menit</option>
                <option value="15m">15 Menit</option>
                <option value="1h">1 Jam</option>
                <option value="1d">1 Hari</option>
                <option value="1wk">1 Minggu</option>
                <option value="1mo">1 Bulan</option>
                </select>
            </div>

            <div className="flex flex-col">
                <label className="text-xs text-gray-500 mb-1">Strategy</label>
                <select 
                  value={selectedStrategy}
                  onChange={(e) => setSelectedStrategy(e.target.value)}
                  className="border p-2 rounded w-40"
                >
                  {STRATEGIES.map(s => (
                    <option key={s.id} value={s.id}>{s.label}</option>
                  ))}
                </select>
            </div>

            <div className="flex flex-col">
                <label className="text-xs text-gray-500 mb-1">Initial Capital (IDR)</label>
                <input 
                  type="number"
                  value={initialCapital}
                  onChange={(e) => setInitialCapital(parseInt(e.target.value))}
                  className="border p-2 rounded w-40"
                  placeholder="10000000"
                />
            </div>

            <button type="submit" className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 h-[42px]">
              Load Chart
            </button>
            <button 
                type="button" 
                onClick={handleBacktest}
                className={`px-4 py-2 text-white rounded h-[42px] ${
                    selectedStrategy === "NONE" ? 'bg-gray-400 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'
                }`}
                disabled={selectedStrategy === "NONE" || backtestLoading}
            >
              {backtestLoading ? "Testing..." : "Test Strategy"}
            </button>
            <button
                type="button"
                onClick={paperStatus?.is_active ? handleStopPaper : handleStartPaper}
                className={`px-4 py-2 text-white rounded h-[42px] ${
                    selectedStrategy === "NONE" && !paperStatus?.is_active ? 'bg-gray-400 cursor-not-allowed' : 
                    paperStatus?.is_active ? 'bg-red-600 hover:bg-red-700' : 'bg-orange-600 hover:bg-orange-700'
                }`}
                disabled={(selectedStrategy === "NONE" && !paperStatus?.is_active) || paperLoading}
            >
                {paperLoading ? "Loading..." : paperStatus?.is_active ? "Stop Auto-Trade" : "Start Auto-Trade"}
            </button>
          </form>

          <Chart symbol={selectedSymbol} interval={selectedInterval} source={marketSource} strategy={selectedStrategy} period={selectedPeriod} />
          <p className="text-sm text-gray-500 mt-2">
            Menampilkan data real-time untuk <strong>{selectedSymbol}</strong> dengan interval <strong>{selectedInterval}</strong> dan periode <strong>{selectedPeriod}</strong> (Sumber: {marketSource}). Update setiap detik.
          </p>
        </section>
      )}

      {/* Paper Trading Section */}
      {paperStatus?.is_active && (
        <section className="bg-white p-6 rounded-lg shadow-md mb-6 border-l-4 border-orange-500">
            <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                    <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                    Live Auto-Trade Simulation: {paperStatus.active_symbol} ({paperStatus.active_strategy})
                </h2>
                <div className="text-xl font-bold">
                    Balance: {new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }).format(paperStatus.balance)}
                </div>
            </div>

            {/* Live Trades Table */}
             <div className="overflow-x-auto">
                 <table className="min-w-full table-auto text-sm border bg-orange-50">
                    <thead className="bg-orange-100">
                        <tr>
                            <th className="px-4 py-2 text-left border">Entry Time</th>
                            <th className="px-4 py-2 text-left border">Symbol</th>
                            <th className="px-4 py-2 text-right border">Entry Price</th>
                            <th className="px-4 py-2 text-right border">Current Price</th>
                            <th className="px-4 py-2 text-center border">Status</th>
                            <th className="px-4 py-2 text-right border">PnL (IDR)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {paperStatus.trades.length === 0 ? (
                             <tr>
                                <td colSpan="6" className="px-4 py-8 text-center text-gray-500 italic">Waiting for signal...</td>
                            </tr>
                        ) : (
                            paperStatus.trades.map((trade, idx) => (
                                <tr key={trade.id} className="border-b bg-white">
                                     <td className="px-4 py-2 border">{new Date(trade.entry_date).toLocaleTimeString()}</td>
                                     <td className="px-4 py-2 border font-bold">{trade.symbol}</td>
                                     <td className="px-4 py-2 text-right border">{trade.entry_price.toLocaleString()}</td>
                                     <td className="px-4 py-2 text-right border">{trade.current_price.toLocaleString()}</td>
                                     <td className={`px-4 py-2 text-center font-bold border ${
                                         trade.status === 'OPEN' ? 'text-blue-600' : 
                                         trade.status === 'WIN' ? 'text-green-600' : 'text-red-600'
                                     }`}>
                                         {trade.status}
                                     </td>
                                     <td className={`px-4 py-2 text-right border font-bold ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                         {new Intl.NumberFormat('id-ID').format(trade.pnl)}
                                     </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                 </table>
            </div>
        </section>
      )}

      {/* Backtest Results Section */}
      {backtestResult && (
        <section className="bg-white p-6 rounded-lg shadow-md mb-6">
            <h2 className="text-xl font-semibold mb-4">Backtest Results: {backtestResult.strategy}</h2>
            
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-gray-50 p-4 rounded border">
                    <div className="text-gray-500 text-sm">Total Trades</div>
                    <div className="text-2xl font-bold">{backtestResult.total_trades}</div>
                </div>
                <div className="bg-gray-50 p-4 rounded border">
                    <div className="text-gray-500 text-sm">Win Rate</div>
                    <div className={`text-2xl font-bold ${backtestResult.win_rate >= 50 ? 'text-green-600' : 'text-red-600'}`}>
                        {backtestResult.win_rate.toFixed(1)}%
                    </div>
                </div>
                 <div className="bg-gray-50 p-4 rounded border">
                    <div className="text-gray-500 text-sm">Wins / Losses</div>
                    <div className="text-2xl font-bold text-gray-800">
                        <span className="text-green-600">{backtestResult.wins}</span> / <span className="text-red-600">{backtestResult.losses}</span>
                    </div>
                </div>
                <div className="bg-gray-50 p-4 rounded border">
                    <div className="text-gray-500 text-sm">Total PnL (IDR)</div>
                    <div className={`text-2xl font-bold ${backtestResult.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR' }).format(backtestResult.total_pnl)}
                    </div>
                </div>
            </div>

            {/* Trade History Table */}
            <div className="overflow-x-auto">
                 <table className="min-w-full table-auto text-sm border">
                    <thead className="bg-gray-100">
                        <tr>
                            <th className="px-4 py-2 text-left border">Entry Date</th>
                            <th className="px-4 py-2 text-left border">Exit Date</th>
                            <th className="px-4 py-2 text-right border">Entry Price</th>
                            <th className="px-4 py-2 text-right border">Exit Price</th>
                             <th className="px-4 py-2 text-center border">Status</th>
                            <th className="px-4 py-2 text-right border">PnL (IDR)</th>
                            <th className="px-4 py-2 text-right border">Balance (IDR)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {backtestResult.trades.map((trade, idx) => (
                            <tr key={idx} className="border-b hover:bg-gray-50">
                                 <td className="px-4 py-2 border">{new Date(trade.entry_date).toLocaleDateString()}</td>
                                 <td className="px-4 py-2 border">{trade.exit_date ? new Date(trade.exit_date).toLocaleDateString() : '-'}</td>
                                 <td className="px-4 py-2 text-right border">{trade.entry_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 })}</td>
                                 <td className="px-4 py-2 text-right border">{trade.exit_price ? trade.exit_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 6 }) : '-'}</td>
                                 <td className={`px-4 py-2 text-center font-bold border ${
                                     trade.status === 'WIN' ? 'text-green-600' : 
                                     trade.status === 'LOSS' ? 'text-red-600' : 'text-yellow-600'
                                 }`}>
                                     {trade.status}
                                 </td>
                                 <td className={`px-4 py-2 text-right border ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                     {new Intl.NumberFormat('id-ID').format(trade.pnl)}
                                 </td>
                                 <td className="px-4 py-2 text-right font-medium border">
                                     {new Intl.NumberFormat('id-ID').format(trade.realized_value)}
                                 </td>
                            </tr>
                        ))}
                         {backtestResult.trades.length === 0 && (
                            <tr>
                                <td colSpan="7" className="px-4 py-4 text-center text-gray-500">No trades executed in this period.</td>
                            </tr>
                        )}
                    </tbody>
                 </table>
            </div>
        </section>
      )}

      {/* Signals Table */}
      <section className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Market Signals Scan</h2>
        
        {error && <div className="text-red-500 mb-4">Error: {error}</div>}
        
        <div className="overflow-x-auto mb-6">
          <table className="min-w-full table-auto">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-4 py-2 text-left">Symbol</th>
                <th className="px-4 py-2 text-right">Price</th>
                <th className="px-4 py-2 text-center">Signal</th>
                <th className="px-4 py-2 text-left">Reasons</th>
                <th className="px-4 py-2 text-right">Time</th>
              </tr>
            </thead>
            <tbody>
              {signals.map((signal) => (
                <tr key={signal.symbol} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-2 font-medium">{signal.symbol}</td>
                  <td className="px-4 py-2 text-right">{signal.price.toFixed(2)}</td>
                  <td className={`px-4 py-2 text-center font-bold ${
                    signal.signal_type === 'BUY' ? 'text-green-600' : 
                    signal.signal_type === 'SELL' ? 'text-red-600' : 'text-yellow-600'
                  }`}>
                    {signal.signal_type}
                  </td>
                  <td className="px-4 py-2 text-sm text-gray-600">
                    {signal.reasons.join(", ") || "-"}
                  </td>
                  <td className="px-4 py-2 text-right text-sm text-gray-500">
                    {new Date(signal.timestamp).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
              {signals.length === 0 && !loading && !error && (
                <tr>
                  <td colSpan="5" className="px-4 py-4 text-center text-gray-500">No signals found.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Watchlist Selection */}
        <div className="border-t pt-4">
            <h3 className="font-semibold mb-2 text-gray-700">Pantau Market (Watchlist)</h3>
            <div className="flex flex-wrap gap-4">
                {WATCHLIST_OPTIONS.map((option) => (
                    <label key={option.id} className="flex items-center space-x-2 cursor-pointer">
                        <input 
                            type="checkbox" 
                            checked={selectedWatchlist.includes(option.id)}
                            onChange={(e) => {
                                if (e.target.checked) {
                                    setSelectedWatchlist([...selectedWatchlist, option.id]);
                                } else {
                                    setSelectedWatchlist(selectedWatchlist.filter(id => id !== option.id));
                                }
                            }}
                            className="form-checkbox h-5 w-5 text-blue-600 rounded"
                        />
                        <span className="text-gray-700">{option.label}</span>
                    </label>
                ))}
            </div>
        </div>
      </section>
    </div>
  );
};

export default Dashboard;