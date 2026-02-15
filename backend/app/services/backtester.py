from typing import List
from app.models.schemas import MarketData, StrategySignal, BacktestSummary, TradeResult
from app.services.strategies import Strategies
from datetime import datetime

class Backtester:
    def __init__(self, data: List[MarketData], initial_capital: float = 10000000, exchange_rate: float = 16000):
        self.data = data
        self.initial_capital = initial_capital # In IDR
        self.exchange_rate = exchange_rate # IDR per USD (1 if stock)
        
    def run(self, strategy_name: str) -> BacktestSummary:
        if strategy_name == "POPGUN":
            signals = Strategies.detect_popgun(self.data)
            return self._test_popgun(signals)
        elif strategy_name == "FVG":
            signals = Strategies.detect_fvg(self.data)
            return self._test_fvg(signals)
        elif strategy_name == "RBD":
            signals = Strategies.detect_rbd(self.data)
            return self._test_rbd(signals)
        else:
            return BacktestSummary(
                strategy=strategy_name,
                total_trades=0,
                wins=0,
                losses=0,
                win_rate=0.0,
                total_pnl=0.0,
                trades=[]
            )

    def _test_popgun(self, signals: List[StrategySignal]) -> BacktestSummary:
        trades = []
        
        # Simple Logic: 
        # For each signal, if price breaks Entry -> Enter Trade.
        # Target: TP1. Stop: SL.
        
        # Map timestamp to index for faster lookup
        ts_map = {d.timestamp: i for i, d in enumerate(self.data)}
        
        for signal in signals:
            idx = ts_map.get(signal.timestamp)
            if idx is None or idx >= len(self.data) - 1:
                continue
                
            targets = signal.metadata.get("targets")
            if not targets:
                continue
                
            # Check Long Setup
            long_setup = targets["long"]
            entry_price = long_setup["entry"]
            tp = long_setup["tp1"]
            sl = long_setup["sl"]
            
            # Look ahead
            trade = None
            for i in range(idx + 1, len(self.data)):
                bar = self.data[i]
                
                # Check Entry
                if trade is None:
                    if bar.high >= entry_price:
                        # Entered Long
                        trade = {
                            "entry_date": bar.timestamp,
                            "entry_price": entry_price,
                            "position": "LONG",
                            "status": "OPEN",
                            "invested": self.initial_capital,
                        }
                        # If gap up above TP, instant win (simplified)
                        if bar.open > tp:
                             trade["exit_price"] = bar.open
                             trade["exit_date"] = bar.timestamp
                             trade["status"] = "WIN"
                             break
                    else:
                        # Entry not triggered yet
                        continue
                
                # Trade is Open, check Exit
                if trade:
                    # Check SL first (conservative)
                    if bar.low <= sl:
                        trade["exit_price"] = sl
                        trade["exit_date"] = bar.timestamp
                        trade["status"] = "LOSS"
                        break
                    
                    # Check TP
                    if bar.high >= tp:
                        trade["exit_price"] = tp
                        trade["exit_date"] = bar.timestamp
                        trade["status"] = "WIN"
                        break
            
            if trade:
                # Calculate PnL
                if trade["status"] == "OPEN":
                    trade["exit_price"] = self.data[-1].close
                    trade["exit_date"] = self.data[-1].timestamp
                
                entry = trade["entry_price"]
                exit_p = trade["exit_price"]
                
                # Calculate PnL %
                pnl_pct = (exit_p - entry) / entry
                
                # Calculate Value
                # Invested (IDR) -> Convert to USD -> Buy Asset
                # USD Amount = Invested / Rate
                usd_capital = trade["invested"] / self.exchange_rate
                
                # Units = USD / EntryPrice
                units = usd_capital / entry
                
                # Final USD = Units * ExitPrice
                final_usd = units * exit_p
                
                # Final IDR = Final USD * Rate
                final_idr = final_usd * self.exchange_rate
                
                pnl_idr = final_idr - trade["invested"]
                
                trades.append(TradeResult(
                    entry_date=trade["entry_date"],
                    exit_date=trade["exit_date"],
                    entry_price=entry,
                    exit_price=exit_p,
                    position="LONG",
                    status=trade["status"],
                    pnl=pnl_idr,
                    pnl_percent=pnl_pct * 100,
                    invested=trade["invested"],
                    realized_value=final_idr
                ))

        # Summarize
        wins = len([t for t in trades if t.status == "WIN"])
        losses = len([t for t in trades if t.status == "LOSS"])
        total = len(trades)
        total_pnl = sum([t.pnl for t in trades])
        
        return BacktestSummary(
            strategy="POPGUN",
            total_trades=total,
            wins=wins,
            losses=losses,
            win_rate=(wins/total * 100) if total > 0 else 0,
            total_pnl=total_pnl,
            trades=trades
        )

    def _test_fvg(self, signals: List[StrategySignal]) -> BacktestSummary:
        trades = []
        ts_map = {d.timestamp: i for i, d in enumerate(self.data)}
        
        for signal in signals:
            idx = ts_map.get(signal.timestamp)
            if idx is None or idx >= len(self.data) - 1:
                continue
            
            # FVG Logic
            # Buy Limit at Top of FVG
            entry_price = signal.metadata["fvg_top"]
            stop_loss = signal.metadata["fvg_bottom"]
            
            # Target: 1.5 Risk
            risk = entry_price - stop_loss
            if risk <= 0: continue
            
            tp = entry_price + (1.5 * risk)
            
            trade = None
            for i in range(idx + 1, len(self.data)):
                bar = self.data[i]
                
                # Prevent same-candle exit if timestamps are identical (e.g. duplicates)
                if bar.timestamp <= signal.timestamp:
                    continue
                
                # Check Entry (Price dips into FVG)
                if trade is None:
                    if bar.low <= entry_price:
                        # Filled
                        trade = {
                            "entry_date": bar.timestamp,
                            "entry_price": entry_price, # Limit fill
                            "position": "LONG",
                            "status": "OPEN",
                            "invested": self.initial_capital,
                        }
                        
                        # Check SL/TP in same bar? (Optimistic)
                        # Let's assume close first for simplicity or standard SL check
                        if bar.low <= stop_loss:
                            trade["exit_price"] = stop_loss
                            trade["exit_date"] = bar.timestamp
                            trade["status"] = "LOSS"
                            break
                        if bar.high >= tp:
                            trade["exit_price"] = tp
                            trade["exit_date"] = bar.timestamp
                            trade["status"] = "WIN"
                            break
                    else:
                        continue
                        
                # If Trade is Open (and not closed in same bar)
                if trade and trade.get("status") == "OPEN":
                    # Check SL
                    if bar.low <= stop_loss:
                        trade["exit_price"] = stop_loss
                        trade["exit_date"] = bar.timestamp
                        trade["status"] = "LOSS"
                        break
                    
                    # Check TP
                    if bar.high >= tp:
                        trade["exit_price"] = tp
                        trade["exit_date"] = bar.timestamp
                        trade["status"] = "WIN"
                        break
            
            if trade:
                 # Calculate PnL (Same logic)
                if trade["status"] == "OPEN":
                    trade["exit_price"] = self.data[-1].close
                    trade["exit_date"] = self.data[-1].timestamp
                
                entry = trade["entry_price"]
                exit_p = trade["exit_price"]
                pnl_pct = (exit_p - entry) / entry
                
                usd_capital = trade["invested"] / self.exchange_rate
                units = usd_capital / entry
                final_usd = units * exit_p
                final_idr = final_usd * self.exchange_rate
                pnl_idr = final_idr - trade["invested"]
                
                trades.append(TradeResult(
                    entry_date=trade["entry_date"],
                    exit_date=trade["exit_date"],
                    entry_price=entry,
                    exit_price=exit_p,
                    position="LONG",
                    status=trade["status"],
                    pnl=pnl_idr,
                    pnl_percent=pnl_pct * 100,
                    invested=trade["invested"],
                    realized_value=final_idr
                ))

        wins = len([t for t in trades if t.status == "WIN"])
        losses = len([t for t in trades if t.status == "LOSS"])
        total = len(trades)
        total_pnl = sum([t.pnl for t in trades])
        
        return BacktestSummary(
            strategy="FVG",
            total_trades=total,
            wins=wins,
            losses=losses,
            win_rate=(wins/total * 100) if total > 0 else 0,
            total_pnl=total_pnl,
            trades=trades
        )

    def _test_rbd(self, signals: List[StrategySignal]) -> BacktestSummary:
        trades = []
        ts_map = {d.timestamp: i for i, d in enumerate(self.data)}
        
        for signal in signals:
            idx = ts_map.get(signal.timestamp)
            if idx is None or idx >= len(self.data) - 1:
                continue
            
            meta = signal.metadata
            entry_price = signal.price
            sl = meta.get("sl")
            tp = meta.get("tp")
            
            if not sl or not tp:
                continue

            trade = {
                "entry_date": signal.timestamp, # Entry at close of signal candle
                "entry_price": entry_price,
                "position": "LONG" if signal.type == "BULLISH" else "SHORT",
                "status": "OPEN",
                "invested": self.initial_capital,
            }

            # Simulate trade starting from NEXT candle
            for i in range(idx + 1, len(self.data)):
                bar = self.data[i]
                
                # Prevent same-candle exit if timestamps are identical (e.g. duplicates)
                if bar.timestamp <= trade["entry_date"]:
                    continue
                
                # Check SL/TP
                if trade["position"] == "LONG":
                    # Check Low for SL
                    if bar.low <= sl:
                        trade["exit_price"] = sl
                        trade["exit_date"] = bar.timestamp
                        trade["status"] = "LOSS"
                        break
                    # Check High for TP
                    if bar.high >= tp:
                        trade["exit_price"] = tp
                        trade["exit_date"] = bar.timestamp
                        trade["status"] = "WIN"
                        break
                else: # SHORT
                    # Check High for SL
                    if bar.high >= sl:
                        trade["exit_price"] = sl
                        trade["exit_date"] = bar.timestamp
                        trade["status"] = "LOSS"
                        break
                    # Check Low for TP
                    if bar.low <= tp:
                        trade["exit_price"] = tp
                        trade["exit_date"] = bar.timestamp
                        trade["status"] = "WIN"
                        break

            # Calculate PnL if trade closed or still open
            if trade["status"] == "OPEN":
                trade["exit_price"] = self.data[-1].close
                trade["exit_date"] = self.data[-1].timestamp
            
            entry = trade["entry_price"]
            exit_p = trade["exit_price"]
            
            if trade["position"] == "LONG":
                pnl_pct = (exit_p - entry) / entry
            else:
                pnl_pct = (entry - exit_p) / entry
            
            # Value Calc
            # Invested (IDR) -> Convert to USD -> Buy Asset
            usd_capital = trade["invested"] / self.exchange_rate
            
            # Simplified PnL
            pnl_usd = usd_capital * pnl_pct
            pnl_idr = pnl_usd * self.exchange_rate
            
            trades.append(TradeResult(
                entry_date=trade["entry_date"],
                exit_date=trade["exit_date"],
                entry_price=entry,
                exit_price=exit_p,
                position=trade["position"],
                status=trade["status"],
                pnl=pnl_idr,
                pnl_percent=pnl_pct * 100,
                invested=trade["invested"],
                realized_value=trade["invested"] + pnl_idr
            ))

        wins = len([t for t in trades if t.status == "WIN"])
        losses = len([t for t in trades if t.status == "LOSS"])
        total = len(trades)
        total_pnl = sum([t.pnl for t in trades])
        
        return BacktestSummary(
            strategy="RBD",
            total_trades=total,
            wins=wins,
            losses=losses,
            win_rate=(wins/total * 100) if total > 0 else 0,
            total_pnl=total_pnl,
            trades=trades
        )
