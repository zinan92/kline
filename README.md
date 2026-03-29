# kline

Multi-asset K-line data. Give it a ticker and timeframe, get back OHLCV candles.

```
in:  ticker + timeframe + date range
out: standardized OHLCV candles (open, high, low, close, volume)
```

Supports **A-shares**, **US stocks**, **crypto**, and **commodities** through a single API.

## Quick Start

```bash
git clone https://github.com/zinan92/kline.git
cd kline
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Optional: add TuShare token for A-share data
cp .env.example .env
# edit .env with your KLINE_TUSHARE_TOKEN

python -m kline
```

Server starts at `http://localhost:8100`. Open `/docs` for the interactive API.

## API

### Get candles

```
GET /api/candles/{asset_class}/{ticker}?timeframe=1d&limit=100
```

| Param | Example | Description |
|-------|---------|-------------|
| `asset_class` | `us_stock` | `a_share`, `us_stock`, `crypto`, `commodity` |
| `ticker` | `AAPL` | Stock symbol, crypto base (BTC), or alias (GOLD) |
| `timeframe` | `1d` | `1m`, `5m`, `30m`, `1h`, `1d`, `1w` |
| `start` | `2026-01-01` | Start date (YYYY-MM-DD) |
| `end` | `2026-03-28` | End date (YYYY-MM-DD) |
| `refresh` | `true` | Force re-fetch from source |

**Response:**

```json
{
  "ticker": "AAPL",
  "asset_class": "us_stock",
  "timeframe": "1d",
  "count": 3,
  "candles": [
    {"timestamp": "2026-03-26", "open": 178.5, "high": 182.3, "low": 177.8, "close": 181.2, "volume": 52340000},
    {"timestamp": "2026-03-27", "open": 181.2, "high": 183.1, "low": 179.5, "close": 180.8, "volume": 48120000},
    {"timestamp": "2026-03-28", "open": 180.8, "high": 185.0, "low": 180.2, "close": 184.5, "volume": 55670000}
  ]
}
```

### Examples

```bash
# US stock — daily
curl "localhost:8100/api/candles/us_stock/AAPL?timeframe=1d&limit=30"

# A-share — daily (requires TuShare token)
curl "localhost:8100/api/candles/a_share/000001?timeframe=1d"

# Crypto — 1 hour
curl "localhost:8100/api/candles/crypto/BTC?timeframe=1h&limit=100"

# Commodity — gold daily
curl "localhost:8100/api/candles/commodity/GOLD?timeframe=1d"
```

### Commodity aliases

| Alias | Resolves to |
|-------|------------|
| GOLD, XAUUSD | GC=F |
| SILVER, XAGUSD | SI=F |
| OIL, CRUDE, WTI | CL=F |
| BRENT | BZ=F |
| NATGAS | NG=F |
| COPPER | HG=F |
| CORN | ZC=F |

## Data Sources

| Asset Class | Source | Auth Required |
|-------------|--------|--------------|
| A-shares | TuShare Pro | Yes (free token) |
| US stocks | Yahoo Finance | No |
| Crypto | Binance public API | No |
| Commodities | Yahoo Finance futures | No |

## How It Works

1. Request comes in → check local SQLite cache
2. Cache hit → return candles
3. Cache miss → fetch from upstream provider → save to cache → return
4. `?refresh=true` → skip cache, always fetch fresh

Data is stored in `data/kline.db` (SQLite with WAL mode). No external database needed.

## Development

```bash
pip install -e ".[dev]"
pytest
pytest --cov=kline
```

## License

MIT
