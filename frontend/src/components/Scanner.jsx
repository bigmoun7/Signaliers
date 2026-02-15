import React, { useState, useEffect } from 'react';

const Scanner = () => {
  // Ensure API URL doesn't have a trailing slash
  const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Scanner specific state
  const [selectedInterval, setSelectedInterval] = useState("1d");
  const [marketSource, setMarketSource] = useState("YAHOO");
  const [selectedWatchlist, setSelectedWatchlist] = useState(['top_crypto']);

  const WATCHLIST_OPTIONS = [
    { id: 'lq45', label: 'IDX LQ45 (Saham)', symbols: ['BBCA', 'BBRI', 'TLKM', 'BMRI', 'ASII', 'GOTO', 'UNVR'] },
    { id: 'tech_us', label: 'US Tech (Saham)', symbols: ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA'] },
    { id: 'top_crypto', label: 'Top Crypto', symbols: ['BTC', 'ETH', 'SOL', 'BNB', 'XRP'] },
    { id: 'meme', label: 'Meme Coins', symbols: ['DOGE', 'SHIB', 'PEPE', 'WIF'] },
  ];

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

      const response = await fetch(`${API_URL}/api/market-scan?${queryParams}`);
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

  useEffect(() => {
    fetchSignals();
    const interval = setInterval(() => {
        fetchSignals();
    }, 5000); // Refresh signals every 5s (slower than dashboard to save resources)
    return () => clearInterval(interval);
  }, [selectedWatchlist, marketSource, selectedInterval]);

  return (
    <div className="container mx-auto p-4 space-y-6">
        <header className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold text-gray-800">Market Signals Scanner</h1>
            <button 
                onClick={fetchSignals}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition"
            >
                Refresh Data
            </button>
        </header>

        {/* Controls */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
            <div className="flex gap-4 mb-4 flex-wrap items-end">
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
                
                <div className="flex flex-col">
                    <label className="text-xs text-gray-500 mb-1">Interval</label>
                    <select 
                        value={selectedInterval}
                        onChange={(e) => setSelectedInterval(e.target.value)}
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
        </div>

      {/* Signals Table */}
      <section className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-xl font-semibold mb-4">Scan Results</h2>
        
        {error && <div className="text-red-500 mb-4">Error: {error}</div>}
        {loading && <div className="text-blue-500 mb-4">Scanning market...</div>}
        
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
      </section>
    </div>
  );
};

export default Scanner;
