# Phase 43: Fixed Income & Bond Portfolio Management — SPEC

## Overview
提供固定收益投資組合管理，支援債券、儲蓄險和定存追蹤，幫助投資者管理利率風險和收益。

## Current State
- ⚠️ 缺乏固定收益資產追蹤
- ⚠️ 缺乏定存/儲蓄險管理
- ⚠️ 缺乏利率風險分析
- ⚠️ 缺乏固定收益儀表板

## Target State
- 🔄 `FixedIncomeService` — 債券 CRUD + 殖利率計算
- 🔄 `TermDepositService` — 定存/儲蓄險追蹤
- 🔄 `BondAnalyticsService` — Duration / 利率敏感度
- 🔄 API 端點 — `/fixed-income`, `/term-deposits`
- 🔄 前端儀表板 — `FixedIncomeDashboard`

## Data Models

### Bond
```
- id, user_id, name, bond_type (gov/corp/muni)
- ticker (optional), face_value, coupon_rate, purchase_price
- purchase_date, maturity_date, yield_to_maturity
- credit_rating, current_market_value, unrealized_pnl
- currency
```

### TermDeposit
```
- id, user_id, name, bank_name
- principal, interest_rate, term_months
- start_date, maturity_date, compound_frequency
- accrued_interest, auto_renew, notes
```

## Services

### FixedIncomeService
- `create_bond()`, `get_bond()`, `list_bonds()`, `update_bond()`, `delete_bond()`
- `calculate_yield_to_maturity()` — YTM 計算
- `calculate_current_yield()` — 當前殖利率
- `get_bond_summary()` — 總覽統計

### BondAnalyticsService
- `calculate_duration()` — Macauley Duration
- `calculate_modified_duration()`
- `calculate_interest_rate_sensitivity()` — 殖利率變動對價格影響
- `get_yield_curve_visualization_data()` — 殖利率曲線數據

### TermDepositService
- `create_term_deposit()`, `get_term_deposit()`, `list_term_deposits()`
- `calculate_accrued_interest()` — 應計利息
- `calculate_maturity_value()` — 到期本利和
- `get_maturity_reminders()` — 30/60/90 天到期提醒

## API Endpoints

### Bonds
- `POST /api/v1/fixed-income/bonds` — 建立債券
- `GET /api/v1/fixed-income/bonds` — 列表
- `GET /api/v1/fixed-income/bonds/{id}` — 詳情
- `PUT /api/v1/fixed-income/bonds/{id}` — 更新
- `DELETE /api/v1/fixed-income/bonds/{id}` — 刪除
- `GET /api/v1/fixed-income/bonds/{id}/analytics` — 風除分析
- `GET /api/v1/fixed-income/bonds/summary` — 總覽

### Term Deposits
- `POST /api/v1/fixed-income/term-deposits` — 建立定存
- `GET /api/v1/fixed-income/term-deposits` — 列表
- `GET /api/v1/fixed-income/term-deposits/{id}` — 詳情
- `PUT /api/v1/fixed-income/term-deposits/{id}` — 更新
- `DELETE /api/v1/fixed-income/term-deposits/{id}` — 刪除
- `GET /api/v1/fixed-income/term-deposits/maturity-alerts` — 到期提醒

## Acceptance Criteria
- [ ] 債券 CRUD + 殖利率計算正確
- [ ] 定存追蹤正常，到期提醒可用
- [ ] Duration 分析可用
- [ ] 固定收益儀表板顯示配置總覽
- [ ] 後端測試覆蓋
