from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AccountProvider(ABC):
    @abstractmethod
    async def get_summary(self) -> dict[str, Any]: ...


class MarketDataProvider(ABC):
    @abstractmethod
    async def get_candles(
        self, symbol: str, timeframe: str, count: int
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_ticks(
        self, symbol: str, limit: int
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_symbols(self) -> list[str]: ...


class TradeProvider(ABC):
    @abstractmethod
    async def get_open_positions(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def open_trade(
        self, symbol: str, lot: float, order_type: str
    ) -> dict[str, Any]: ...

    @abstractmethod
    async def close_trade(self, ticket: int) -> dict[str, Any]: ...

    @abstractmethod
    async def get_trade_history(self) -> list[dict[str, Any]]: ...


class LogProvider(ABC):
    @abstractmethod
    async def get_logs(
        self, limit: int, severity: str
    ) -> list[dict[str, Any]]: ...
