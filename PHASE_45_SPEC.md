# Phase 45: Initial Public Offering (IPO) Tracking & Alerts — SPEC

## Overview
提供 IPO 追蹤和上市前的投資機會分析，幫助投資者掌握新上市股票的機會。

## Target State
- 🔄 `IPOService` — IPO CRUD + 上市前分析
- 🔄 `IPOCalendarService` — IPO 日曆管理
- 🔄 `IPOAlertService` — IPO 警報管理
- 🔄 API 端點 — `/ipos`
- 🔄 前端儀表板 — `IPODashboard.tsx`
- 🔄 模型 — `IPORecord`, `IPOAlert`
- 🔄 Schema — `IPOCreate`, `IPOResponse`, `IPOResponse`
- 🔄 Service — `IPOService`
- 🔄 Router — `/api/v1/ipos`

## Data Models

### IPOStatus (Enum)
`upcoming`, `filing`, `allocated`, `listed`, `withdrawn`

### IPORecord
```
- id, user_id, company_name, ticker (optional pre-IPO)
- exchange, sector, industry
- ipo_price_min, ipo_price_max, final_ipo_price
- shares_offered, lot_size, oversubscription_ratio
- application_deadline, listing_date, first_trading_date
- underwriter, status, estimated_market_cap, raising_amount
- notes, is_active, created_at, updated_at
```

### IPOAlert
```
- id, user_id, ipo_id, alert_type (deadline/allocation/performance)
- is_active, triggered_at, message
```

## Services

### IPOService
- `create_ipo()`, `get_ipo()`, `list_ipos()`, `update_ipo()`, `delete_ipo()`
- `get_upcoming_ipos()` — 即將上市的 IPO
- `get_ipo_analysis()` — IPO 估值分析（承銷商、同業比較）
- `compare_with_peers()` — 行業比較
- `get_ipo_performance()` — 上市後績效

### IPOCalendarService
- `get_calendar()` — IPO 日曆總覽
- `get_upcoming_deadlines()` — 即將截止的申請
- `get_first_day_stats()` — 首日表現統計

### IPOAlertService
- `create_alert()`, `get_alerts()`, `delete_alert()`
- `check_deadline_alerts()`, `track_allocation_results()`

## API Endpoints

### IPO Management
- `POST /api/v1/ipos/` — 建立 IPO 記錄
- `GET /api/v1/ipos/` — 列表 (篩選: status, sector, date_range)
- `GET /api/v1/ipos/{id}` — 詳情
- `PUT /api/v1/ipos/{id}` — 更新
- `DELETE /api/v1/ipos/{id}` — 刪除
- `GET /api/v1/ipos/upcoming` — 即將上市
- `GET /api/v1/ipos/analysis/{id}` — 分析報告
- `GET /api/v1/ipos/performance/{id}` — 上市後績效

### Calendar
- `GET /api/v1/ipos/calendar` — IPO 日曆
- `GET /api/v1/ipos/deadlines` — 申請截止日
- `GET /api/v1/ipos/stats/first-day` — 首日表現統計

### Alerts
- `POST /api/v1/ipos/alerts` — 建立警報
- `GET /api/v1/ipos/alerts` — 列表
- `DELETE /api/v1/ipos/alerts/{id}` — 刪除

## Frontend Components

### IPODashboard.tsx
- IPO Calendar view
- Upcoming IPOs list with countdown
- IPO analysis cards
- Alert configuration panel
