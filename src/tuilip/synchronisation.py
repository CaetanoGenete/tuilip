import asyncio
from dataclasses import dataclass, field
from math import fmod
import time


@dataclass(slots=True)
class Clock:
    period: float
    start: float = field(default_factory=time.monotonic, init=False)

    def delta(self) -> float:
        return self.period - fmod(time.monotonic() - self.start, self.period)

    async def synca(self) -> None:
        await asyncio.sleep(self.delta())

    def sync(self) -> None:
        time.sleep(self.delta())
