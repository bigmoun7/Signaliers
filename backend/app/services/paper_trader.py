import asyncio
import json
import uuid
import os
from datetime import datetime
from typing import List, Dict, Optional
from app.models.schemas import PaperTrade, PaperTradingStatus
from app.services.fetcher import fetcher
from app.services.strategies import Strategies

DATA_FILE = "paper_trades.json"

class PaperTradingService:
    def __init__(self):
        self.is_running = False
        self.active_symbol = None
        self.active_strategy = None
        self.initial_capital = 10000000.0 # IDR
        self.current_balance = 10000000.0
        self.trades: List[PaperTrade] = []
        self.active_trade: Optional[PaperTrade] = None
        self.interval = "1m" # Fast interval for demo
        self.task = None
        self.exchange_rate = 16000.0 
        
        self.load_state()

    def load_state(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                    self.trades = [PaperTrade(**t) for t in data.get("trades", [])]
                    # Restore active trade if any (simplified: just take the first OPEN one)
                    open_trades = [t for t in self.trades if t.status == "OPEN"]
                    if open_trades:
                        self.active_trade = open_trades[0]
                        self.active_symbol = self.active_trade.symbol
                        self.active_strategy = self.active_trade.strategy
                        self.is_running = True # Auto-resume? Maybe wait for user.
                        # For safety, don't auto-run, just restore state
                        self.is_running = False 
                        self.active_trade = None # Reset active trade until user restarts
            except Exception as e:
                print(f"Failed to load state: {e}")

    def save_state(self):
        try:
            data = {
                "trades": [t.dict() for t in self.trades]
            }
            # Convert datetime to ISO string for JSON
            # Pydantic .dict() keeps datetime objects, need .json() or manual conversion
            # Actually using jsonable_encoder or custom serializer is better
            # Simple approach: Pydantic .json()
            with open(DATA_FILE, "w") as f:
                f.write(json.dumps(json.loads(PaperTradingStatus(
                    is_active=self.is_running,
                    trades=self.trades,
                    balance=self.current_balance
                ).json())["trades"], indent=2))
        except Exception as e:
            print(f"Failed to save state: {e}")

    def start(self, symbol: str, strategy: str, capital: float = 10000000):
        if self.is_running:
            return {"status": "error", "message": "Bot already running"}
            
        self.is_running = True
        self.active_symbol = symbol
        self.active_strategy = strategy
        self.initial_capital = capital
        self.current_balance = capital
        # self.trades = [] # Keep history!
        
        # Check if we have an open trade for this symbol/strategy
        for t in self.trades:
            if t.status == "OPEN" and t.symbol == symbol and t.strategy == strategy:
                self.active_trade = t
                break
        else:
            self.active_trade = None
        
        self.task = asyncio.create_task(self._run_loop())
        return {"status": "success", "message": f"Started {strategy} bot on {symbol}"}

    def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()
            self.task = None
        return {"status": "success", "message": "Bot stopped"}

    def get_status(self) -> PaperTradingStatus:
        return PaperTradingStatus(
            is_active=self.is_running,
            active_symbol=self.active_symbol,
            active_strategy=self.active_strategy,
            trades=self.trades,
            balance=self.current_balance
        )

    async def _run_loop(self):
        print(f"Bot Loop Started for {self.active_symbol}")
        loop = asyncio.get_event_loop()
        
        while self.is_running:
            try:
                # 1. Fetch Latest Data (Run in Executor to avoid blocking)
                data = await loop.run_in_executor(None, lambda: fetcher.get_historical_data(
                    self.active_symbol, 
                    interval=self.interval, 
                    limit=50, 
                    source="BINANCE" if self.active_symbol in ["BTC", "ETH", "SOL"] else "YAHOO"
                ))
                
                if not data:
                    await asyncio.sleep(5)
                    continue

                latest_candle = data[-1]
                current_price = latest_candle.close

                # 2. Manage Active Trade
                if self.active_trade:
                    # Update current PnL
                    self.active_trade.current_price = current_price
                    pnl_usd = (current_price - self.active_trade.entry_price) * self.active_trade.quantity
                    pnl_idr = pnl_usd * self.exchange_rate
                    
                    self.active_trade.pnl = pnl_idr
                    self.active_trade.pnl_percent = ((current_price - self.active_trade.entry_price) / self.active_trade.entry_price) * 100
                    
                    # Exit Logic (Simple Demo)
                    entry = self.active_trade.entry_price
                    tp = entry * 1.02 # 2% Target
                    sl = entry * 0.99 # 1% Stop
                    
                    should_close = False
                    status = "OPEN"
                    
                    if current_price >= tp:
                        should_close = True
                        status = "WIN"
                    elif current_price <= sl:
                        should_close = True
                        status = "LOSS"
                        
                    if should_close:
                        self.active_trade.status = status
                        self.active_trade.exit_price = current_price
                        self.active_trade.exit_date = datetime.now()
                        self.current_balance += pnl_idr
                        
                        # Update list (find and replace)
                        # Since active_trade is a reference to an item in self.trades or new
                        # If it's new, we need to add it? No, we added it on entry.
                        # Wait, in previous code I inserted on close.
                        # Better: Add to list ON ENTRY with status OPEN. Update in place.
                        
                        self.active_trade = None
                        self.save_state()
                        print(f"Trade Closed: {status} PnL: {pnl_idr}")
                    else:
                        # Just update state?
                        pass

                # 3. Check for New Entry
                if not self.active_trade:
                    signal = None
                    if self.active_strategy == "POPGUN":
                        signals = Strategies.detect_popgun(data)
                        if signals:
                            last_signal = signals[-1]
                            if (latest_candle.timestamp - last_signal.timestamp).total_seconds() < 3600:
                                targets = last_signal.metadata["targets"]["long"]
                                if current_price > targets["entry"]:
                                    signal = "BUY"
                    
                    elif self.active_strategy == "FVG":
                        signals = Strategies.detect_fvg(data)
                        if signals:
                            last_signal = signals[-1]
                            fvg_top = last_signal.metadata["fvg_top"]
                            if current_price <= fvg_top:
                                signal = "BUY"

                    if signal == "BUY":
                         invest_amount_idr = self.current_balance * 0.1
                         invest_amount_usd = invest_amount_idr / self.exchange_rate
                         quantity = invest_amount_usd / current_price
                         
                         new_trade = PaperTrade(
                             id=str(uuid.uuid4()),
                             symbol=self.active_symbol,
                             strategy=self.active_strategy,
                             entry_date=datetime.now(),
                             entry_price=current_price,
                             quantity=quantity,
                             initial_capital=invest_amount_idr,
                             current_price=current_price,
                             pnl=0,
                             pnl_percent=0,
                             status="OPEN"
                         )
                         
                         self.trades.insert(0, new_trade)
                         self.active_trade = new_trade
                         self.save_state()
                         print(f"Trade Opened: {self.active_symbol} @ {current_price}")

            except Exception as e:
                print(f"Error in Bot Loop: {e}")
            
            await asyncio.sleep(2) # Check every 2 seconds

# Singleton
paper_trader = PaperTradingService()
