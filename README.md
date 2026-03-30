<div align="center">

# kline

**多资产 K 线数据服务 — 一个 ticker + 一个 timeframe，返回标准化 OHLCV 蜡烛图**

[![Python](https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

```
in  ticker + timeframe (1m/5m/30m/1h/1d/1w) + date range
out OHLCV candles (timestamp, open, high, low, close, volume)

fail ticker not found     → search suggestions
fail data source down     → fallback to cache / stale warning
fail timeframe not supported → supported list
fail A-share no token     → setup instructions
```

Providers: `tushare` (A股), `yahoo` (美股/商品), `binance` (加密货币)

## 示例输出

```bash
$ curl "localhost:8100/api/candles/us_stock/AAPL?timeframe=1d&limit=3"
```

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

```bash
# A股日线 (需要 TuShare token)
$ curl "localhost:8100/api/candles/a_share/000001?timeframe=1d"

# 加密货币 1 小时线
$ curl "localhost:8100/api/candles/crypto/BTC?timeframe=1h&limit=100"

# 商品 — 黄金日线
$ curl "localhost:8100/api/candles/commodity/GOLD?timeframe=1d"
```

## 架构

```
Request ▶ API ▶ 本地缓存命中? ─yes─▶ 返回 candles
                     │
                    no
                     │
                     ▼
              选择 Provider
           ┌─────┬─────┬──────┐
           │     │     │      │
        TuShare Yahoo Binance Yahoo
        (A股)  (美股)  (加密) (商品)
           │     │     │      │
           └─────┴─────┴──────┘
                     │
                     ▼
              保存到 SQLite ▶ 返回 candles
```

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/zinan92/kline.git
cd kline

# 2. 安装依赖
python -m venv .venv && source .venv/bin/activate
pip install -e .

# 3. 配置 A 股数据源 (可选，美股/加密/商品无需配置)
cp .env.example .env
# 编辑 .env 填入 TUSHARE_TOKEN (免费申请: tushare.pro)

# 4. 启动服务
python -m kline
# 访问 http://localhost:8100/docs 查看交互式 API 文档
```

## API 参考

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/candles/{asset_class}/{ticker}` | 获取 K 线蜡烛图数据 |
| `GET` | `/api/tickers` | 列出本地已缓存的 ticker |
| `GET` | `/api/health` | 健康检查 |

### 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `asset_class` | path | — | `a_share` / `us_stock` / `crypto` / `commodity` |
| `ticker` | path | — | 代码: `000001`, `AAPL`, `BTC`, `GOLD` |
| `timeframe` | query | `1d` | `1m` / `5m` / `30m` / `1h` / `1d` / `1w` |
| `start` | query | — | 起始日期 `YYYY-MM-DD` |
| `end` | query | — | 结束日期 `YYYY-MM-DD` |
| `limit` | query | `500` | 返回蜡烛数量上限 (1-2000) |
| `refresh` | query | `false` | `true` 强制从上游重新拉取 |

### 商品别名

| 别名 | Yahoo Finance 代码 |
|------|-------------------|
| `GOLD`, `XAUUSD` | GC=F |
| `SILVER`, `XAGUSD` | SI=F |
| `OIL`, `CRUDE`, `WTI` | CL=F |
| `BRENT` | BZ=F |
| `NATGAS` | NG=F |
| `COPPER` | HG=F |
| `CORN`, `WHEAT`, `SOYBEAN` | ZC=F, ZW=F, ZS=F |

## 数据源

| 资产类别 | Provider | 认证 | 支持 Timeframe |
|---------|----------|------|---------------|
| A股 | TuShare Pro | 需要 token (免费) | 1d, 1w |
| 美股 | Yahoo Finance | 无需 | 1m, 5m, 30m, 1h, 1d, 1w |
| 加密货币 | Binance 公开 API | 无需 | 1m, 5m, 30m, 1h, 1d, 1w |
| 商品期货 | Yahoo Finance | 无需 | 1m, 5m, 30m, 1h, 1d, 1w |

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 运行时 | Python 3.11+ | 核心语言 |
| 框架 | FastAPI | REST API |
| 存储 | SQLite (WAL mode) | 本地缓存，无需外部数据库 |
| 验证 | Pydantic v2 | 请求/响应模型 |

## 项目结构

```
kline/
├── src/kline/
│   ├── app.py              # FastAPI 应用
│   ├── api.py              # 3 个 API 端点
│   ├── models.py           # Candle 数据模型 + 枚举
│   ├── store.py            # SQLite 存储 (upsert + query)
│   ├── registry.py         # Provider 注册与初始化
│   ├── config.py           # 环境变量配置
│   └── providers/
│       ├── base.py         # Provider Protocol 接口
│       ├── ashare.py       # TuShare Pro (A股)
│       ├── us.py           # Yahoo Finance (美股)
│       ├── crypto.py       # Binance 公开 API (加密货币)
│       └── commodity.py    # Yahoo Finance 期货 + 别名
├── tests/                  # 19 tests
├── data/                   # SQLite 数据库 (自动创建)
├── .env.example
└── pyproject.toml
```

## 配置

| 变量 | 说明 | 必填 | 默认值 |
|------|------|------|--------|
| `KLINE_TUSHARE_TOKEN` | TuShare Pro token (A股数据) | A股必填 | — |
| `KLINE_DB_PATH` | SQLite 数据库路径 | 否 | `data/kline.db` |
| `KLINE_PORT` | 服务端口 | 否 | `8100` |
| `KLINE_REQUEST_TIMEOUT` | 上游请求超时 (秒) | 否 | `30` |

## For AI Agents

### Capability Contract

```yaml
name: kline
version: 0.1.0
capability:
  summary: "Multi-asset K-line data service. Give it a ticker + timeframe, get back OHLCV candles."
  in: "ticker + timeframe + optional date range"
  out: "standardized OHLCV candles (timestamp, open, high, low, close, volume)"
  fail:
    - "ticker not found → suggestions list"
    - "data source down → cached data or stale warning"
    - "timeframe not supported → supported timeframes list"
    - "A-share no token → setup instructions"
  providers: [tushare, yahoo, binance]
api_base_url: http://localhost:8100
endpoints:
  - path: /api/candles/{asset_class}/{ticker}
    method: GET
    description: "Get OHLCV candles"
    params:
      - name: asset_class
        type: string
        enum: [a_share, us_stock, crypto, commodity]
        required: true
      - name: ticker
        type: string
        required: true
      - name: timeframe
        type: string
        enum: ["1m", "5m", "30m", "1h", "1d", "1w"]
        default: "1d"
      - name: limit
        type: integer
        default: 500
  - path: /api/tickers
    method: GET
    description: "List cached tickers"
  - path: /api/health
    method: GET
    description: "Health check"
install_command: "pip install -e ."
start_command: "python -m kline"
health_check: "GET /api/health"
```

### Agent 调用示例

```python
import httpx

async def get_candles(ticker: str, asset_class: str = "us_stock", timeframe: str = "1d"):
    """获取任意资产的 K 线数据"""
    base = "http://localhost:8100"
    resp = await httpx.AsyncClient().get(
        f"{base}/api/candles/{asset_class}/{ticker}",
        params={"timeframe": timeframe, "limit": 100},
    )
    return resp.json()["candles"]

# 美股
candles = await get_candles("AAPL")

# A股
candles = await get_candles("000001", "a_share")

# 加密货币 1 小时线
candles = await get_candles("BTC", "crypto", "1h")

# 黄金
candles = await get_candles("GOLD", "commodity")
```

## 相关项目

| 项目 | 说明 | 链接 |
|------|------|------|
| quant-data-pipeline | 原始全功能量化数据平台 (kline 从中拆出) | [zinan92/quant-data-pipeline](https://github.com/zinan92/quant-data-pipeline) |
| trading-copilot | AI 交易分析终端 (44 种方法论) | [zinan92/trading-copilot](https://github.com/zinan92/trading-copilot) |

## License

MIT
