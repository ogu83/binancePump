from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Union

@dataclass
class PriceChange:
    symbol: str
    prev_price: float
    price: float
    total_trades: int
    open_price: float
    volume: float
    is_printed: bool
    event_time: datetime
    prev_volume: float

    def __repr__(self) -> str:
        return (
            f"PriceChange(symbol={self.symbol!r}, prev_price={self.prev_price:.2f}, "
            f"price={self.price:.2f}, total_trades={self.total_trades}, "
            f"open_price={self.open_price:.2f}, volume={self.volume:.2f}, "
            f"is_printed={self.is_printed}, event_time={self.event_time!r}, "
            f"prev_volume={self.prev_volume:.2f})"
        )

    @property
    def volume_change(self) -> float:
        """Absolute change in volume since last tick."""
        return self.volume - self.prev_volume

    @property
    def volume_change_perc(self) -> float:
        """Volume change as a percentage of previous volume."""
        if self.prev_volume == 0:
            return 0.0
        return (self.volume_change / self.prev_volume) * 100

    @property
    def price_change(self) -> float:
        """Absolute change in price since last tick."""
        return self.price - self.prev_price

    @property
    def price_change_perc(self) -> float:
        """Price change as a percentage of previous price."""
        if self.prev_price == 0:
            return 0.0
        return (self.price_change / self.prev_price) * 100

    def is_pump(self, lim_perc: float) -> bool:
        """
        Returns True if price has risen by at least lim_perc percent.
        """
        return self.price_change_perc >= lim_perc

    def is_dump(self, lim_perc: float) -> bool:
        """
        Returns True if price has fallen by at least lim_perc percent.
        (lim_perc may be provided as positive or negative—this normalizes it.)
        """
        threshold = -abs(lim_perc)
        return self.price_change_perc <= threshold
