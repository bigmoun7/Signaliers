import React, { useState, useEffect } from 'react';
import Chart from './Chart';

const Dashboard = () => {
  // Ensure API URL doesn't have a trailing slash
  const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

  const [selectedSymbol, setSelectedSymbol] = useState("BTC");
  const [selectedInterval, setSelectedInterval] = useState("1d");
  const [assetType, setAssetType] = useState("CRYPTO"); // CRYPTO, STOCK
  const [marketSource, setMarketSource] = useState("YAHOO"); // YAHOO, BINANCE, COINGECKO, STOCKBIT
  const [selectedStrategy, setSelectedStrategy] = useState("NONE"); // NONE, POPGUN
  const [selectedPeriod, setSelectedPeriod] = useState("1y");

  const STRATEGIES = [
    { id: 'NONE', label: 'No Strategy' },
    { id: 'POPGUN', label: 'PopGun Pattern' },
    { id: 'FVG', label: 'Smart Money Concept (FVG)' },
    { id: 'RBD', label: 'Rally Base Drop (RBD)' }
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
  
  const [isChartVisible, setIsChartVisible] = useState(true);
  
  // Backtest State
  const [backtestResult, setBacktestResult] = useState(null);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [backtestError, setBacktestError] = useState(null);
  const [initialCapital, setInitialCapital] = useState(10000000);

  // Paper Trading State
  const [paperStatus, setPaperStatus] = useState(null);
  const [paperLoading, setPaperLoading] = useState(false);

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

        const response = await fetch(`${API_URL}/api/backtest/${selectedStrategy}/${selectedSymbol}?${queryParams}`);
        
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
          const response = await fetch(`${API_URL}/api/paper/status`);
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
          await fetch(`${API_URL}/api/paper/start?symbol=${selectedSymbol}&strategy=${selectedStrategy}&capital=${initialCapital}`, { method: 'POST' });
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
          await fetch(`${API_URL}/api/paper/stop`, { method: 'POST' });
          fetchPaperStatus();
      } catch (err) {
          console.error(err);
      } finally {
          setPaperLoading(false);
      }
  };

  useEffect(() => {
    fetchPaperStatus();
    const interval = setInterval(() => {
        fetchPaperStatus();
    }, 1000); 
    return () => clearInterval(interval);
  }, []);

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
      
      {/* Paper Trading Section - Top Priority if Active */}
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

      {/* Chart Section */}
      {isChartVisible && (
        <section className="bg-white p-6 rounded-lg shadow-md mb-6">
          <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Live Market Chart (TradingView Style)</h2>
          </div>
          
          <form onSubmit={handleSymbolSubmit} className="mb-6 space-y-4">
            {/* Control Groups */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                
                {/* Group 1: Data Source */}
                <div className="bg-gray-50 p-3 rounded border">
                    <h3 className="text-xs font-bold text-gray-400 uppercase mb-2">Data Source</h3>
                    <div className="space-y-2">
                         <div className="flex flex-col">
                            <label className="text-xs text-gray-500 mb-1">Type</label>
                            <select 
                            value={assetType}
                            onChange={(e) => setAssetType(e.target.value)}
                            className="border p-2 rounded w-full"
                            >
                            <option value="STOCK">Saham</option>
                            <option value="CRYPTO">Kripto</option>
                            </select>
                        </div>
                        <div className="flex flex-col">
                            <label className="text-xs text-gray-500 mb-1">Provider</label>
                            <select 
                            value={marketSource}
                            onChange={(e) => setMarketSource(e.target.value)}
                            className="border p-2 rounded w-full"
                            >
                            <option value="YAHOO">Yahoo Finance</option>
                            <option value="BINANCE">Binance</option>
                            <option value="COINGECKO">Coin Gecko</option>
                            <option value="STOCKBIT">Stockbit</option>
                            </select>
                        </div>
                    </div>
                </div>

                {/* Group 2: Asset Settings */}
                <div className="bg-gray-50 p-3 rounded border">
                    <h3 className="text-xs font-bold text-gray-400 uppercase mb-2">Asset Settings</h3>
                    <div className="space-y-2">
                        <div className="flex flex-col">
                            <label className="text-xs text-gray-500 mb-1">Symbol</label>
                            <input 
                            type="text" 
                            value={selectedSymbol}
                            onChange={handleSymbolChange}
                            className="border p-2 rounded w-full uppercase"
                            placeholder="Symbol (e.g. BTC)" 
                            />
                        </div>
                        <div className="flex gap-2">
                            <div className="flex flex-col w-1/2">
                                <label className="text-xs text-gray-500 mb-1">Period</label>
                                <select 
                                value={selectedPeriod}
                                onChange={(e) => setSelectedPeriod(e.target.value)}
                                className="border p-2 rounded w-full"
                                >
                                {PERIOD_OPTIONS.map(opt => (
                                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                                ))}
                                </select>
                            </div>
                            <div className="flex flex-col w-1/2">
                                <label className="text-xs text-gray-500 mb-1">Interval</label>
                                <select 
                                value={selectedInterval}
                                onChange={handleIntervalChange}
                                className="border p-2 rounded w-full"
                                >
                                <option value="1m">1 M</option>
                                <option value="5m">5 M</option>
                                <option value="15m">15 M</option>
                                <option value="1h">1 H</option>
                                <option value="1d">1 D</option>
                                <option value="1wk">1 W</option>
                                <option value="1mo">1 Mo</option>
                                </select>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Group 3: Strategy Settings */}
                <div className="bg-gray-50 p-3 rounded border">
                    <h3 className="text-xs font-bold text-gray-400 uppercase mb-2">Strategy & Risk</h3>
                    <div className="space-y-2">
                         <div className="flex flex-col">
                            <label className="text-xs text-gray-500 mb-1">Strategy</label>
                            <select 
                            value={selectedStrategy}
                            onChange={(e) => setSelectedStrategy(e.target.value)}
                            className="border p-2 rounded w-full"
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
                            className="border p-2 rounded w-full"
                            placeholder="10000000"
                            />
                        </div>
                    </div>
                </div>

                {/* Group 4: Actions */}
                <div className="bg-gray-50 p-3 rounded border flex flex-col justify-between">
                     <h3 className="text-xs font-bold text-gray-400 uppercase mb-2">Actions</h3>
                     <div className="flex flex-col gap-2">
                        <button type="submit" className="w-full px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
                        Update Chart
                        </button>
                        
                        <div className="flex gap-2">
                            <button 
                                type="button" 
                                onClick={handleBacktest}
                                className={`w-1/2 px-2 py-2 text-white rounded text-sm ${
                                    selectedStrategy === "NONE" ? 'bg-gray-400 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-700'
                                }`}
                                disabled={selectedStrategy === "NONE" || backtestLoading}
                            >
                            {backtestLoading ? "Testing..." : "Backtest"}
                            </button>
                            <button
                                type="button"
                                onClick={paperStatus?.is_active ? handleStopPaper : handleStartPaper}
                                className={`w-1/2 px-2 py-2 text-white rounded text-sm ${
                                    selectedStrategy === "NONE" && !paperStatus?.is_active ? 'bg-gray-400 cursor-not-allowed' : 
                                    paperStatus?.is_active ? 'bg-red-600 hover:bg-red-700' : 'bg-orange-600 hover:bg-orange-700'
                                }`}
                                disabled={(selectedStrategy === "NONE" && !paperStatus?.is_active) || paperLoading}
                            >
                                {paperLoading ? "..." : paperStatus?.is_active ? "Stop Auto" : "Start Auto"}
                            </button>
                        </div>
                     </div>
                </div>

            </div>
          </form>

          <Chart symbol={selectedSymbol} interval={selectedInterval} source={marketSource} strategy={selectedStrategy} period={selectedPeriod} />
          <p className="text-sm text-gray-500 mt-2">
            Menampilkan data real-time untuk <strong>{selectedSymbol}</strong> dengan interval <strong>{selectedInterval}</strong> dan periode <strong>{selectedPeriod}</strong> (Sumber: {marketSource}). Update setiap detik.
          </p>
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
    </div>
  );
};

export default Dashboard;
