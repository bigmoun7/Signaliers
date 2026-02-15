import React, { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

const Chart = ({ symbol, interval, source, strategy, period }) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const volumeSeriesRef = useRef(null);
  const expectedVolumeSeriesRef = useRef(null);
  const markersRef = useRef([]); // Store markers to clear them if needed
  const priceLinesRef = useRef([]); // Store price lines to clear them
  const signalsRef = useRef([]); // Store signals for tooltip lookup

  const [tooltip, setTooltip] = React.useState(null);
  const [lastSignal, setLastSignal] = React.useState(null);

  // Ensure API URL doesn't have a trailing slash
  const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

  const [currentPrice, setCurrentPrice] = React.useState(null);

  // Main Chart Effect: Create Chart, Fetch History, Draw Strategy
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart instance
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'white' },
        textColor: 'black',
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      grid: {
        vertLines: { color: '#e1e1e1' },
        horzLines: { color: '#e1e1e1' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: true,
      },
    });

    chartRef.current = chart;

    // Add candlestick series
    const newSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
      priceFormat: {
        type: 'price',
        precision: 2,
        minMove: 0.01,
      },
    });

    seriesRef.current = newSeries;

    // Fetch historical data
    const fetchHistory = async () => {
      try {
        const p = period || '1y';
        const response = await fetch(`${API_URL}/api/history/${symbol}?interval=${interval}&source=${source || 'YAHOO'}&period=${p}`);
        if (!response.ok) throw new Error("Failed to fetch history");
        const data = await response.json();
        
        // Convert timestamp strings to UNIX seconds
        const formattedData = data.map(d => ({
          time: new Date(d.timestamp).getTime() / 1000, // Unix timestamp in seconds
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
        })).sort((a, b) => a.time - b.time); // Ensure sorted

        // Dynamic Precision Logic
        if (formattedData.length > 0) {
            const lastPrice = formattedData[formattedData.length - 1].close;
            let precision = 2;
            let minMove = 0.01;

            if (lastPrice < 1) {
                precision = 6;
                minMove = 0.000001;
            } else if (lastPrice < 1000) {
                precision = 4;
                minMove = 0.0001;
            }

            newSeries.applyOptions({
                priceFormat: {
                    type: 'price',
                    precision: precision,
                    minMove: minMove,
                },
            });
        }

        newSeries.setData(formattedData);
        chart.timeScale().fitContent();
        
        // Fetch Strategy Data if selected
        if (strategy && strategy !== "NONE") {
             if (strategy === "POPGUN") {
                 const stratResponse = await fetch(`${API_URL}/api/strategy/popgun/${symbol}?interval=${interval}&source=${source || 'YAHOO'}&period=${p}`);
                 if (stratResponse.ok) {
                     const signals = await stratResponse.json();
                     signalsRef.current = signals;
                     setLastSignal(signals[signals.length - 1]);
                     
                     // 1. Add Markers for PopGun Bars
                     const markers = signals.map(s => ({
                         time: new Date(s.timestamp).getTime() / 1000,
                         position: 'aboveBar',
                         color: '#e91e63',
                         shape: 'arrowDown',
                         text: 'PG',
                         size: 2,
                     }));
                     newSeries.setMarkers(markers);
                     
                     // 2. Draw Price Lines for the LATEST PopGun only (to avoid clutter)
                     if (signals.length > 0) {
                         const lastSignal = signals[signals.length - 1];
                         const targets = lastSignal.metadata.targets;
                         
                         // Clear previous lines
                         priceLinesRef.current = [];
                         
                         const createLine = (price, color, title) => {
                             const line = newSeries.createPriceLine({
                                 price: price,
                                 color: color,
                                 lineWidth: 1,
                                 lineStyle: 2, // Dashed
                                 axisLabelVisible: true,
                                 title: title,
                             });
                             priceLinesRef.current.push(line);
                         };
                         
                         // Draw Lines
                         createLine(targets.long.entry, 'blue', 'Long Entry');
                         createLine(targets.long.tp1, 'green', 'L TP1');
                         createLine(targets.long.tp2, 'green', 'L TP2');
                         createLine(targets.long.tp3, 'green', 'L TP3');
                         
                         createLine(targets.short.entry, 'orange', 'Short Entry');
                         createLine(targets.short.tp1, 'red', 'S TP1');
                         createLine(targets.short.tp2, 'red', 'S TP2');
                         createLine(targets.short.tp3, 'red', 'S TP3');
                     }
                 }
             } else if (strategy === "FVG") {
                 const stratResponse = await fetch(`${API_URL}/api/strategy/fvg/${symbol}?interval=${interval}&source=${source || 'YAHOO'}&period=${p}`);
                 if (stratResponse.ok) {
                     const signals = await stratResponse.json();
                     signalsRef.current = signals;
                     setLastSignal(signals[signals.length - 1]);
                     
                     // Add Markers
                     const markers = signals.map(s => ({
                         time: new Date(s.timestamp).getTime() / 1000,
                         position: 'belowBar',
                         color: '#00bcd4',
                         shape: 'arrowUp',
                         text: 'FVG',
                         size: 2,
                     }));
                     newSeries.setMarkers(markers);
                     
                     // Draw FVG Zones for the LAST few signals (e.g. last 3)
                     if (signals.length > 0) {
                         const recentSignals = signals.slice(-3);
                         priceLinesRef.current = [];
                         
                         recentSignals.forEach((sig, idx) => {
                             const { fvg_top, fvg_bottom } = sig.metadata;
                             const opacity = idx === recentSignals.length - 1 ? 1 : 0.5; // Older ones are faded
                             
                             // Top Line
                             const lineTop = newSeries.createPriceLine({
                                 price: fvg_top,
                                 color: `rgba(0, 188, 212, ${opacity})`,
                                 lineWidth: 1,
                                 lineStyle: 0, // Solid
                                 axisLabelVisible: true,
                                 title: `FVG Top ${idx+1}`,
                             });
                             priceLinesRef.current.push(lineTop);

                             // Bottom Line
                             const lineBottom = newSeries.createPriceLine({
                                 price: fvg_bottom,
                                 color: `rgba(0, 188, 212, ${opacity})`,
                                 lineWidth: 1,
                                 lineStyle: 0, // Solid
                                 axisLabelVisible: true,
                                 title: `FVG Bot ${idx+1}`,
                             });
                             priceLinesRef.current.push(lineBottom);
                         });
                     }
                 }
             } else if (strategy === "RBD") {
                 const stratResponse = await fetch(`${API_URL}/api/strategy/rbd/${symbol}?interval=${interval}&source=${source || 'YAHOO'}&period=${p}`);
                 if (stratResponse.ok) {
                     const signals = await stratResponse.json();
                     signalsRef.current = signals;
                     setLastSignal(signals[signals.length - 1]);
                     
                     const markers = [];
                     
                     signals.forEach(s => {
                         const isBull = s.type === 'BULLISH';
                         markers.push({
                             time: new Date(s.timestamp).getTime() / 1000,
                             position: isBull ? 'belowBar' : 'aboveBar',
                             color: isBull ? '#4caf50' : '#f44336', // Green / Red
                             shape: isBull ? 'arrowUp' : 'arrowDown',
                             text: isBull ? 'BUY' : 'SELL',
                             size: 2, // Make it visible
                         });
                     });
                     newSeries.setMarkers(markers);

                     // Draw SL/TP Lines for the LATEST Signal
                     if (signals.length > 0) {
                         const lastSignal = signals[signals.length - 1];
                         const { sl, tp } = lastSignal.metadata;
                         
                         priceLinesRef.current = [];
                         
                         // Helper to create line
                         const createLine = (price, color, title) => {
                             if (!price) return;
                             const line = newSeries.createPriceLine({
                                 price: price,
                                 color: color,
                                 lineWidth: 2,
                                 lineStyle: 0, // Solid
                                 axisLabelVisible: true,
                                 title: title,
                             });
                             priceLinesRef.current.push(line);
                         };
                         
                         const isBull = lastSignal.type === 'BULLISH';
                         
                         // Draw SL
                         createLine(sl, '#ff5252', 'Stop Loss');
                         
                         // Draw TP
                         createLine(tp, '#00e676', 'Take Profit');
                         
                         // Draw Entry Price line for reference
                         createLine(lastSignal.price, isBull ? '#4caf50' : '#f44336', isBull ? 'Entry Buy' : 'Entry Sell');
                     }
                 }
             } else if (strategy === "AURA") {
                 const stratResponse = await fetch(`${API_URL}/api/strategy/aura/${symbol}?interval=${interval}&source=${source || 'YAHOO'}&period=${p}`);
                 if (stratResponse.ok) {
                     const signals = await stratResponse.json();
                     signalsRef.current = signals;
                     setLastSignal(signals[signals.length - 1]);
                     
                     const markers = [];
                     
                     signals.forEach(s => {
                         const isBull = s.type === 'BULLISH';
                         markers.push({
                             time: new Date(s.timestamp).getTime() / 1000,
                             position: isBull ? 'belowBar' : 'aboveBar',
                             color: isBull ? '#00ffbb' : '#ff0055', // Aura Green / Red
                             shape: isBull ? 'arrowUp' : 'arrowDown',
                             text: isBull ? 'BUY' : 'SELL',
                             size: 2,
                         });
                     });
                     newSeries.setMarkers(markers);

                     // Draw SL/TP Lines for the LATEST Signal
                     if (signals.length > 0) {
                         const lastSignal = signals[signals.length - 1];
                         const { sl, tp } = lastSignal.metadata;
                         
                         priceLinesRef.current = [];
                         
                         // Helper to create line
                         const createLine = (price, color, title) => {
                             if (!price) return;
                             const line = newSeries.createPriceLine({
                                 price: price,
                                 color: color,
                                 lineWidth: 2,
                                 lineStyle: 0, // Solid
                                 axisLabelVisible: true,
                                 title: title,
                             });
                             priceLinesRef.current.push(line);
                         };
                         
                         const isBull = lastSignal.type === 'BULLISH';
                         
                         // Draw SL
                         createLine(sl, '#ff5252', 'Stop Loss');
                         
                         // Draw TP
                         createLine(tp, '#00e676', 'Take Profit');
                         
                         // Draw Entry Price line for reference
                        createLine(lastSignal.price, isBull ? '#00ffbb' : '#ff0055', isBull ? 'Entry Buy' : 'Entry Sell');
                    }
                }
            } else if (strategy === "VOLUME_SURPRISE") {
                // 1. Fetch Indicator Data (Series)
                try {
                    const indResponse = await fetch(`${API_URL}/api/indicator/volume_surprise/${symbol}?interval=${interval}&source=${source || 'YAHOO'}&period=${p}`);
                    if (indResponse.ok) {
                        const indData = await indResponse.json();
                        
                        // Setup Volume Scale (Overlay)
                        chart.priceScale('volume').applyOptions({
                            scaleMargins: {
                                top: 0.75, // Volume takes bottom 25%
                                bottom: 0,
                            },
                        });

                        // Create Volume Series
                        const volSeries = chart.addHistogramSeries({
                            priceFormat: { type: 'volume' },
                            priceScaleId: 'volume',
                            title: 'Volume',
                        });
                        volumeSeriesRef.current = volSeries;

                        // Create Expected Volume Series (Line)
                        const expSeries = chart.addLineSeries({
                            priceScaleId: 'volume', // Overlay on same scale
                            color: '#ff9800', // Orange
                            lineWidth: 2,
                            lineStyle: 0, // Solid
                            title: 'Exp. Vol',
                            crosshairMarkerVisible: false,
                        });
                        expectedVolumeSeriesRef.current = expSeries;

                        const volData = [];
                        const expData = [];
                        
                        indData.forEach(d => {
                            const time = new Date(d.timestamp).getTime() / 1000;
                            const isSurprise = d.volume > d.expected_volume * 2.0; 
                            
                            // Volume Color Logic
                            let color;
                            if (isSurprise) {
                                color = d.is_bullish ? '#00e676' : '#ff5252'; // Bright Green/Red
                            } else {
                                color = d.is_bullish ? 'rgba(38, 166, 154, 0.3)' : 'rgba(239, 83, 80, 0.3)'; // Faded
                            }

                            volData.push({
                                time: time,
                                value: d.volume,
                                color: color,
                            });

                            expData.push({
                                time: time,
                                value: d.expected_volume,
                            });
                        });

                        volSeries.setData(volData);
                        expSeries.setData(expData);
                    }
                } catch (err) {
                    console.error("Error fetching volume indicator:", err);
                }

                // 2. Fetch Signals (for Markers & Last Signal Panel)
                const stratResponse = await fetch(`${API_URL}/api/strategy/volume_surprise/${symbol}?interval=${interval}&source=${source || 'YAHOO'}&period=${p}`);
                if (stratResponse.ok) {
                    const signals = await stratResponse.json();
                    signalsRef.current = signals;
                    setLastSignal(signals[signals.length - 1]);
                    
                    const markers = [];
                    
                    signals.forEach(s => {
                        const isBull = s.type === 'BULLISH';
                        const volRatio = s.metadata.volume_ratio ? `x${s.metadata.volume_ratio}` : 'VOL';
                        markers.push({
                            time: new Date(s.timestamp).getTime() / 1000,
                            position: isBull ? 'belowBar' : 'aboveBar',
                            color: isBull ? '#7e57c2' : '#ff7043', // Purple / Orange
                            shape: isBull ? 'arrowUp' : 'arrowDown',
                            text: volRatio,
                            size: 2,
                        });
                    });
                    newSeries.setMarkers(markers);
                    
                    // Draw SL/TP for latest
                    if (signals.length > 0) {
                        const lastSignal = signals[signals.length - 1];
                        const { sl, tp } = lastSignal.metadata;
                        
                        priceLinesRef.current = [];
                        
                        const createLine = (price, color, title) => {
                            if (!price) return;
                            const line = newSeries.createPriceLine({
                                price: price,
                                color: color,
                                lineWidth: 2,
                                lineStyle: 0,
                                axisLabelVisible: true,
                                title: title,
                            });
                            priceLinesRef.current.push(line);
                        };
                        
                        const isBull = lastSignal.type === 'BULLISH';
                        createLine(sl, '#ff5252', 'Stop Loss');
                        createLine(tp, '#00e676', 'Take Profit');
                        createLine(lastSignal.price, isBull ? '#7e57c2' : '#ff7043', 'Entry');
                    }
                }
            }

        }
        
      } catch (err) {
        console.error("Error fetching history:", err);
      }
    };

    fetchHistory();

    // Subscribe to crosshair move
    chart.subscribeCrosshairMove((param) => {
      if (
        param.point === undefined ||
        !param.time ||
        param.point.x < 0 ||
        param.point.x > chartContainerRef.current.clientWidth ||
        param.point.y < 0 ||
        param.point.y > chartContainerRef.current.clientHeight
      ) {
        setTooltip(null);
        return;
      }

      // Find signal at this time
      const hoveredTime = param.time; // Unix timestamp
      const signal = signalsRef.current.find(s => {
          const sTime = new Date(s.timestamp).getTime() / 1000;
          return Math.abs(sTime - hoveredTime) < 1; // Tolerance 1s
      });

      if (signal) {
          const dateStr = new Date(signal.timestamp).toLocaleString();
          setTooltip({
              x: param.point.x,
              y: param.point.y,
              content: (
                  <div className="p-2 text-xs">
                      <div className="font-bold mb-1">{signal.name}</div>
                      <div className="mb-1">{dateStr}</div>
                      <div className={`font-bold ${signal.type === 'BULLISH' ? 'text-green-500' : 'text-red-500'}`}>
                          {signal.type} @ {signal.price}
                      </div>
                      {signal.metadata.sl && <div>SL: {signal.metadata.sl.toFixed(2)}</div>}
                      {signal.metadata.tp && <div>TP: {signal.metadata.tp.toFixed(2)}</div>}
                      {signal.metadata.reason && <div className="mt-1 opacity-75 italic">{signal.metadata.reason}</div>}
                      {signal.metadata.volume_ratio && <div>Vol Ratio: x{signal.metadata.volume_ratio}</div>}
                  </div>
              )
          });
      } else {
          setTooltip(null);
      }
    });

    const handleResize = () => {
      chart.applyOptions({ width: chartContainerRef.current.clientWidth });
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [symbol, interval, source, strategy, period]);

  // Real-time updates polling
  useEffect(() => {
    if (!symbol) return;

    const intervalId = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/api/latest/${symbol}?interval=${interval}&source=${source || 'YAHOO'}&_t=${Date.now()}`);
        if (!response.ok) return;
        const d = await response.json();
        
        if (d && seriesRef.current) {
          setCurrentPrice(d.close);
          
          let candleTime = new Date(d.timestamp).getTime() / 1000;

          // Force update the last candle if the new data is for the same period
          // This fixes potential timezone mismatches or slight time differences
          const data = seriesRef.current.data();
          if (data.length > 0) {
            const lastCandle = data[data.length - 1];
            // Check if within same interval window (approximate)
            // 1wk = 604800, 1d = 86400
            const diff = Math.abs(candleTime - lastCandle.time);
            
            // If the time is very close (e.g. less than 1 interval), snap to last candle time
            // For 1wk, if diff < 4 days, assume same week.
            // For 1d, if diff < 12 hours, assume same day.
            let threshold = 0;
            if (interval === '1wk') threshold = 4 * 86400;
            else if (interval === '1d') threshold = 12 * 3600;
            else if (interval === '1mo') threshold = 15 * 86400;
            else threshold = 60; // For intraday

            if (diff < threshold) {
                 candleTime = lastCandle.time;
            }
          }

          const candle = {
            time: candleTime,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
          };
          seriesRef.current.update(candle);
        }
      } catch (err) {
        console.error("Realtime update failed:", err);
      }
    }, 1000); // Poll every 1 second

    return () => clearInterval(intervalId);
  }, [symbol, interval, source]);

  return (
    <div className="relative w-full">
      {currentPrice && (
          <div className="absolute top-2 right-14 z-10 bg-white/90 backdrop-blur px-2 py-1 rounded shadow text-xs font-mono border border-gray-200">
              Live: {currentPrice}
          </div>
      )}

      {lastSignal && (
          <div className="absolute top-2 left-2 z-10 bg-black/80 text-white p-2 rounded text-xs border border-gray-700 shadow-lg pointer-events-none min-w-[120px]">
              <div className="font-bold border-b border-gray-600 mb-1 pb-1 text-gray-300">Last Signal</div>
              <div className={`text-lg font-bold mb-1 ${lastSignal.type === 'BULLISH' ? 'text-green-400' : 'text-red-400'}`}>
                  {lastSignal.type}
              </div>
              <div className="grid grid-cols-2 gap-x-2 gap-y-1">
                  <div className="text-gray-400">Entry:</div>
                  <div className="text-right">{lastSignal.price}</div>
                  
                  {lastSignal.metadata.sl && <><div className="text-gray-400">SL:</div><div className="text-right text-red-300">{lastSignal.metadata.sl.toFixed(2)}</div></>}
                  {lastSignal.metadata.tp && <><div className="text-gray-400">TP:</div><div className="text-right text-green-300">{lastSignal.metadata.tp.toFixed(2)}</div></>}
              </div>
              <div className="text-gray-500 text-[10px] mt-2 text-center">{new Date(lastSignal.timestamp).toLocaleString()}</div>
          </div>
      )}
      
      {tooltip && (
          <div 
              className="absolute z-20 bg-black/90 text-white rounded border border-gray-600 shadow-xl pointer-events-none"
              style={{
                  left: tooltip.x + 10,
                  top: tooltip.y + 10,
              }}
          >
              {tooltip.content}
          </div>
      )}
      
      <div ref={chartContainerRef} className="w-full h-[400px]" />
    </div>
  );
};

export default Chart;
