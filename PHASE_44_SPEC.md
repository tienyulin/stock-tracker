# Phase 44: Commodities & Precious Metals Tracking — SPEC

## Overview
追蹤商品期貨和貴金屬投資組合，支援黃金、白銀、原油、農產品等，讓投資者掌握另類資產。

## Current State
- ⚠️ 缺乏商品期貨追蹤
- ⚠️ 缺乏貴金屬即時報價整合
- ⚠️ 缺乏商品投資儀表板
- ⚠️ 缺乏期貨到期追蹤

## Target State
- 🔄 `CommodityService` — 商品 CRUD + 報價
- 🔄 `PreciousMetalsService` — 貴金屬整合
- 🔄 `FuturesContractService` — 期貨合約追蹤
- 🔄 API 端點 — `/commodities`
- 🔄 前端儀表板 — `CommodityDashboard`

## Data Models

### CommodityPosition
```
- id, user_id, name, commodity_type (gold/silver/oil/agricultural)
- ticker (optional), quantity, unit (oz/g/barrel/bushel)
- purchase_price, current_price, market_value
- purchase_date, notes, currency
```

### FuturesContract
```
- id, user_id, name, commodity_type
- contract_size, contract_month, expiration_date
- entry_price, current_price, market_value
- position_type (long/short), margin_required
- realized_pnl, unrealized_pnl, notes
```

## Services

### CommodityService
- `create_position()`, `get_position()`, `list_positions()`, `update_position()`, `delete_position()`
- `sync_prices()` — 抓取即時報價 (Yahoo Finance)
- `get_commodity_summary()` — 總覽統計
- Commodity types: gold (GC=F), silver (SI=F), oil (CL=F), natural gas (NG=F)

### PreciousMetalsService
- `get_gold_price()`, `get_silver_price()`, `get_platinum_price()`
- `get_historical_data()` — 歷史報價
- `get_market_correlation()` — 與股市相關性
- `get_inflation_hedge_metrics()` — 通膨避險指標

### FuturesContractService
- `create_contract()`, `get_contract()`, `list_contracts()`
- `calculate_margin_requirement()` — 保證金計算
- `get_expiration_alerts()` — 到期提醒 (30/60/90天)
- `calculate_pnl()` — 已實現/未實現損益

## API Endpoints

### Commodities
- `POST /api/v1/commodities/positions` — 建立商品倉位
- `GET /api/v1/commodities/positions` — 列表
- `GET /api/v1/commodities/positions/{id}` — 詳情
- `PUT /api/v1/commodities/positions/{id}` — 更新
- `DELETE /api/v1/commodities/positions/{id}` — 刪除
- `POST /api/v1/commodities/positions/sync-prices` — 同步報價
- `GET /api/v1/commodities/positions/summary` — 總覽

### Futures
- `POST /api/v1/commodities/futures` — 建立期貨合約
- `GET /api/v1/commodities/futures` — 列表
- `GET /api/v1/commodities/futures/{id}` — 詳情
- `PUT /api/v1/commodities/futures/{id}` — 更新
- `DELETE /api/v1/commodities/futures/{id}` — 刪除
- `GET /api/v1/commodities/futures/expiration-alerts` — 到期提醒

### Precious Metals
- `GET /api/v1/commodities/precious-metals/prices` — 即時報價
- `GET /api/v1/commodities/precious-metals/history` — 歷史數據
- `GET /api/v1/commodities/precious-metals/correlation` — 相關性分析

## Acceptance Criteria
- [ ] 商品倉位 CRUD 正常
- [ ] 黃金/白銀/原油 ETF 即時報價正確
- [ ] 期貨到期提醒可用
- [ ] 商品儀表板顯示配置總覽
- [ ] 後端測試覆蓋
