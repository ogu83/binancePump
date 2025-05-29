from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List

@dataclass
class PriceGroup:
    symbol: str
    tick_count: int
    total_price_change: float
    relative_price_change: float
    total_volume_change: float
    last_price: float
    last_event_time: datetime
    open_price: float
    volume: float
    is_printed: bool = field(default=False, repr=False)
    
    def __post_init__(self):
        # ensure correct types at runtime (optional)
        assert isinstance(self.symbol, str)
        assert isinstance(self.tick_count, int)
        # …etc…

    def __getitem__(self, key: str) -> object:
        return getattr(self, key)

    @property
    def console_color(self) -> str:
        return "red" if self.relative_price_change < 0 else "green"

    def to_string(self, is_colored: bool) -> str:
        self.is_printed = True
        base = (
            f"Symbol:{self.symbol}\t"
            f"Time:{self.last_event_time}\t"
            f"Ticks:{self.tick_count}\t"
            f"RPCh:{self.relative_price_change:.2f}\t"
            f"TPCh:{self.total_price_change:.2f}\t"
            f"VCh:{self.total_volume_change:.2f}\t"
            f"LP:{self.last_price}\t"
            f"LV:{self.volume}\t"
        )
        if not is_colored:
            return base
        from termcolor import colored
        return colored(base, self.console_color)