# Phase 41: ESG & Sustainable Investing Tools — SPEC

## Overview
提供完整的 ESG 投資工具，幫助投資者追踪環境、社會和公司治理指標，並提供道德投資組合分析。

## Current State
- ⚠️ 缺乏 ESG 分數追蹤
- ⚠️ 缺乏碳足跡計算
- ⚠️ 缺乏爭議警報系統
- ⚠️ 缺乏 ESG 投資組合建議

## Target State
- 🔄 `EsgService` — ESG 分數 + 碳足跡 + 爭議查詢
- 🔄 `EsgScoresService` — 個別股票 ESG 分數
- 🔄 `CarbonFootprintService` — 碳足跡計算
- 🔄 `ControversyAlertService` — 爭議警報
- 🔄 `EsgPortfolioService` — 投資組合整體 ESG 分析
- 🔄 API 端點 — `/esg`
- 🔄 前端儀表板 — `EsgDashboard`

## Data Models

### EsgScore
```
- id, user_id, ticker, company_name
- esg_total_score (0-100)
- environmental_score, social_score, governance_score
- carbon_footprint_tons, water_usage_m3, waste_tons
- data_source (msci/sustainalytics/trucost)
- last_updated, rating_date
```

### ControversyAlert
```
- id, user_id, ticker, controversy_type (human_rights/weapons/tobacco/gambling/supply_chain)
- severity (low/medium/high/critical)
- headline, description, source_url
- alert_date, status (active/dismissed/resolved)
```

### ExclusionList
```
- id, user_id, list_type (negative_screening/ethical_exclusion)
- sector, ticker, company_name
- reason, created_at, is_active
```

## Services

### EsgService
- `get_esg_score(user_id, ticker)` — 取得個別股票 ESG 分數
- `get_portfolio_esg_score(user_id)` — 計算投資組合整體分數
- `get_esg_trend(user_id, ticker, months)` — 月度趨勢

### CarbonFootprintService
- `calculate_carbon_footprint(user_id)` — 計算整體碳足跡
- `get_carbon_intensity(user_id, ticker)` — 噸 CO2/年
- `compare_to_benchmark(user_id)` — 與市場平均比較

### ControversyAlertService
- `check_controversies(user_id, ticker)` — 檢查爭議
- `get_active_alerts(user_id)` — 取得活躍警報
- `dismiss_alert(alert_id)` — 關閉警報
- `get_exclusion_list(user_id)` — 取得排除名單

### EsgPortfolioService
- `get_esg_rating_distribution(user_id)` — 分數分布
- `get_sustainable_alternatives(user_id, ticker)` — 建議替代
- `screen_portfolio(user_id)` — 負面剔除篩選

## API Endpoints

```
GET  /api/v1/esg/scores/{ticker}          — 個別股票 ESG 分數
GET  /api/v1/esg/portfolio/summary         — 投資組合整體 ESG
GET  /api/v1/esg/portfolio/carbon          — 碳足跡報告
GET  /api/v1/esg/alerts                   — 爭議警報列表
POST /api/v1/esg/alerts/{id}/dismiss      — 關閉警報
GET  /api/v1/esg/exclusions               — 排除名單
POST /api/v1/esg/exclusions               — 新增排除
GET  /api/v1/esg/alternatives/{ticker}    — 永續替代建議
```

## Acceptance Criteria
- [ ] ESG 分數顯示正確（0-100，來源標注）
- [ ] 碳足跡計算準確（噸 CO2/年）
- [ ] 爭議警報正常觸發
- [ ] 替代方案推薦可用
- [ ] 投資組合整體 ESG 分數計算正確
- [ ] 負面剔除名單可自訂管理
