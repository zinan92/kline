"""SQLite storage — save and query candles."""

from __future__ import annotations

from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session, sessionmaker

from kline.models import AssetClass, Base, Candle, KlineRow, Timeframe


class KlineStore:
    """Thin wrapper around SQLite for candle CRUD."""

    def __init__(self, db_path: str) -> None:
        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)
        # Enable WAL mode for concurrent reads
        event.listen(self._engine, "connect", self._enable_wal)
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    @staticmethod
    def _enable_wal(dbapi_conn, _connection_record) -> None:
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    def query(
        self,
        ticker: str,
        asset_class: AssetClass,
        timeframe: Timeframe,
        *,
        start: str | None = None,
        end: str | None = None,
        limit: int = 500,
    ) -> list[Candle]:
        """Query candles for a ticker. Returns oldest-first."""
        with self._session_factory() as session:
            stmt = (
                select(KlineRow)
                .where(
                    KlineRow.ticker == ticker,
                    KlineRow.asset_class == asset_class.value,
                    KlineRow.timeframe == timeframe.value,
                )
                .order_by(KlineRow.timestamp.asc())
                .limit(limit)
            )
            if start:
                stmt = stmt.where(KlineRow.timestamp >= start)
            if end:
                stmt = stmt.where(KlineRow.timestamp <= end)

            rows = session.execute(stmt).scalars().all()
            return [row.to_candle() for row in rows]

    def save(
        self,
        ticker: str,
        asset_class: AssetClass,
        timeframe: Timeframe,
        candles: list[Candle],
    ) -> int:
        """Upsert candles. Returns number of rows affected."""
        if not candles:
            return 0

        records = [
            {
                "ticker": ticker,
                "asset_class": asset_class.value,
                "timeframe": timeframe.value,
                "timestamp": c.timestamp,
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume,
                "amount": c.amount,
            }
            for c in candles
        ]

        with self._session_factory() as session:
            stmt = sqlite_insert(KlineRow).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=["ticker", "asset_class", "timeframe", "timestamp"],
                set_={
                    "open": stmt.excluded.open,
                    "high": stmt.excluded.high,
                    "low": stmt.excluded.low,
                    "close": stmt.excluded.close,
                    "volume": stmt.excluded.volume,
                    "amount": stmt.excluded.amount,
                },
            )
            result = session.execute(stmt)
            session.commit()
            return result.rowcount

    def list_tickers(self, asset_class: AssetClass | None = None) -> list[str]:
        """List all tickers with stored data."""
        with self._session_factory() as session:
            stmt = select(KlineRow.ticker).distinct()
            if asset_class:
                stmt = stmt.where(KlineRow.asset_class == asset_class.value)
            return list(session.execute(stmt).scalars().all())

    def count(self, ticker: str, asset_class: AssetClass, timeframe: Timeframe) -> int:
        """Count stored candles for a ticker."""
        from sqlalchemy import func

        with self._session_factory() as session:
            stmt = (
                select(func.count())
                .select_from(KlineRow)
                .where(
                    KlineRow.ticker == ticker,
                    KlineRow.asset_class == asset_class.value,
                    KlineRow.timeframe == timeframe.value,
                )
            )
            return session.execute(stmt).scalar_one()
