import React, { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

const Chart = ({ symbol, interval, source, strategy, period }) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const markersRef = useRef([]); // Store markers to clear them if needed
  const priceLinesRef = useRef([]); // Store price lines to clear them

  // Ensure API URL doesn't have a trailing slash
  const API_URL = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '');

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
                     
                     // 1. Add Markers for PopGun Bars
                     const markers = signals.map(s => ({
                         time: new Date(s.timestamp).getTime() / 1000,
                         position: 'aboveBar',
                         color: '#e91e63',
                         shape: 'arrowDown',
                         text: 'PG',
                     }));
                     newSeries.setMarkers(markers);
                     
                     // 2. Draw Price Lines for the LATEST PopGun only (to avoid clutter)
                     if (signals.length > 0) {
                         const lastSignal = signals[signals.length - 1];
                         const targets = lastSignal.metadata.targets;
                         
                         // Clear previous lines (not really needed since we recreate chart, but good practice if logic changes)
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
                     
                     // Add Markers
                     const markers = signals.map(s => ({
                         time: new Date(s.timestamp).getTime() / 1000,
                         position: 'belowBar',
                         color: '#00bcd4',
                         shape: 'arrowUp',
                         text: 'FVG',
                     }));
                     newSeries.setMarkers(markers);
                     
                     // Draw FVG Zones for the LAST few signals (e.g. last 3)
                     if (signals.length > 0) {
                         // Show up to 3 most recent FVGs to avoid clutter
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
             }
        }
        
      } catch (err) {
        console.error("Error fetching history:", err);
      }
    };

    fetchHistory();

    // Resize handler
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
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
        const response = await fetch(`http://127.0.0.1:8000/api/latest/${symbol}?interval=${interval}&source=${source || 'YAHOO'}`);
        if (!response.ok) return;
        const d = await response.json();
        
        if (seriesRef.current) {
          seriesRef.current.update({
            time: new Date(d.timestamp).getTime() / 1000,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
          });
        }
      } catch (err) {
        console.error("Realtime update failed:", err);
      }
    }, 1000); // Poll every 1 second

    return () => clearInterval(intervalId);
  }, [symbol, interval, source]);

  return (
    <div className="w-full h-[400px] border border-gray-300 rounded-lg overflow-hidden shadow-sm" ref={chartContainerRef} />
  );
};

export default Chart;