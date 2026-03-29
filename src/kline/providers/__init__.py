"""Data providers — one per asset class, all return list[Candle]."""

from kline.providers.base import Provider
from kline.providers.ashare import AShareProvider
from kline.providers.us import USStockProvider
from kline.providers.crypto import CryptoProvider
from kline.providers.commodity import CommodityProvider

__all__ = ["Provider", "AShareProvider", "USStockProvider", "CryptoProvider", "CommodityProvider"]
