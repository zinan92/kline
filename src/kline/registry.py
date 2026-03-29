"""Provider and store registry — wired once at startup."""

from __future__ import annotations

from functools import lru_cache

from kline.config import Settings, ensure_data_dir, get_settings
from kline.models import AssetClass
from kline.providers.ashare import AShareProvider
from kline.providers.base import Provider, ProviderError
from kline.providers.commodity import CommodityProvider
from kline.providers.crypto import CryptoProvider
from kline.providers.us import USStockProvider
from kline.store import KlineStore

_store: KlineStore | None = None
_providers: dict[AssetClass, Provider] = {}


def init(settings: Settings | None = None) -> None:
    """Initialize store and providers. Called once at app startup."""
    global _store, _providers
    s = settings or get_settings()
    ensure_data_dir(s)

    _store = KlineStore(s.db_path)

    # Always available
    _providers[AssetClass.US_STOCK] = USStockProvider()
    _providers[AssetClass.CRYPTO] = CryptoProvider(timeout=s.request_timeout)
    _providers[AssetClass.COMMODITY] = CommodityProvider()

    # A-share requires TuShare token
    if s.tushare_token:
        _providers[AssetClass.A_SHARE] = AShareProvider(s.tushare_token)


def get_store() -> KlineStore:
    if _store is None:
        init()
    return _store  # type: ignore[return-value]


def get_provider(asset_class: AssetClass) -> Provider:
    if not _providers:
        init()
    provider = _providers.get(asset_class)
    if provider is None:
        if asset_class == AssetClass.A_SHARE:
            raise ProviderError(
                "A-share provider not configured",
                suggestions=["Set KLINE_TUSHARE_TOKEN in .env"],
            )
        raise ProviderError(f"No provider for {asset_class.value}")
    return provider
