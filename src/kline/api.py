"""FastAPI routes — the entire public API."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from kline.models import AssetClass, CandleResponse, ErrorResponse, Timeframe
from kline.providers.base import ProviderError
from kline.registry import get_provider, get_store

router = APIRouter()


@router.get(
    "/candles/{asset_class}/{ticker}",
    response_model=CandleResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def get_candles(
    asset_class: AssetClass,
    ticker: str,
    timeframe: Timeframe = Query(default=Timeframe.DAY),
    start: str | None = Query(default=None, description="Start date: YYYY-MM-DD"),
    end: str | None = Query(default=None, description="End date: YYYY-MM-DD"),
    limit: int = Query(default=500, ge=1, le=2000),
    refresh: bool = Query(default=False, description="Force fetch from source"),
) -> CandleResponse:
    """
    Get K-line candles for any asset.

    - **asset_class**: a_share, us_stock, crypto, commodity
    - **ticker**: Symbol (e.g., 000001, AAPL, BTC, GOLD)
    - **timeframe**: 1m, 5m, 30m, 1h, 1d, 1w
    - **refresh**: Force re-fetch from upstream source
    """
    store = get_store()

    # Try local store first (unless refresh requested)
    if not refresh:
        candles = store.query(ticker, asset_class, timeframe, start=start, end=end, limit=limit)
        if candles:
            return CandleResponse(
                ticker=ticker,
                asset_class=asset_class,
                timeframe=timeframe,
                count=len(candles),
                candles=candles,
            )

    # Fetch from upstream provider
    provider = get_provider(asset_class)
    try:
        candles = await provider.fetch(ticker, timeframe, start=start, end=end, limit=limit)
    except ProviderError as e:
        raise HTTPException(
            status_code=404 if "No data" in str(e) else 400,
            detail=ErrorResponse(
                error=str(e),
                suggestions=e.suggestions,
            ).model_dump(),
        )

    # Save to local store
    if candles:
        store.save(ticker, asset_class, timeframe, candles)

    return CandleResponse(
        ticker=ticker,
        asset_class=asset_class,
        timeframe=timeframe,
        count=len(candles),
        candles=candles,
    )


@router.get("/tickers")
async def list_tickers(
    asset_class: AssetClass | None = Query(default=None),
) -> dict:
    """List all tickers with stored data."""
    store = get_store()
    tickers = store.list_tickers(asset_class)
    return {"count": len(tickers), "tickers": tickers}


@router.get("/health")
async def health() -> dict:
    """Health check."""
    return {"status": "ok", "service": "kline", "version": "0.1.0"}
