from typing import List
from app.models.schemas import MarketData, StrategySignal

from .popgun import detect_popgun
from .fvg import detect_fvg
from .rbd import detect_rbd
from .aura import detect_aura
from .volume_surprise import detect_volume_surprise, analyze_volume_surprise
from .utils import calculate_atr

class Strategies:
    @staticmethod
    def detect_popgun(data: List[MarketData]) -> List[StrategySignal]:
        return detect_popgun(data)

    @staticmethod
    def detect_fvg(data: List[MarketData]) -> List[StrategySignal]:
        return detect_fvg(data)

    @staticmethod
    def detect_rbd(data: List[MarketData]) -> List[StrategySignal]:
        return detect_rbd(data)
    
    @staticmethod
    def detect_aura(data: List[MarketData]) -> List[StrategySignal]:
        return detect_aura(data)
    
    @staticmethod
    def detect_volume_surprise(data: List[MarketData]) -> List[StrategySignal]:
        return detect_volume_surprise(data)

    @staticmethod
    def analyze_volume_surprise(data: List[MarketData]) -> List[dict]:
        return analyze_volume_surprise(data)

    @staticmethod
    def _calculate_atr(data: List[MarketData], period: int = 14) -> List[float]:
        return calculate_atr(data, period)
