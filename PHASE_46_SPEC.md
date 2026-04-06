# Phase 46: Alternative Investments & Private Markets — SPEC

## Overview
支援另類投資和私募市場資產追蹤，包括私募股权、房地产投资信托（REITs）、對沖基金等。

## Architecture

### New Tables
1. **alternative_investments** — 主表：名稱、類型、流動性分類、購買日期、成本基礎
2. **private_fund_nav** — 基金淨值歷史（季度/年度更新）
3. **hedge_fund_holdings** — 對沖基金持倉（FoHF）

### New Services
1. **AlternativeInvestmentService** — CRUD + 組合管理
2. **PrivateFundService** — PE/VC 基金份額與 NAV 追蹤
3. **REITService** — 上市/非上市 REITs 報價與分析
4. **HedgeFundService** — 對沖基金 NAV 與相關性計算

### API Endpoints
- `GET /alternative-investments/summary` — 另類資產總覽
- `GET /alternative-investments/holdings` — 持倉列表
- `POST /alternative-investments/private-funds` — 新增私募基金
- `PUT /alternative-investments/private-funds/{id}/nav` — 更新基金 NAV
- `GET /alternative-investments/reits` — REITs 持倉與報價
- `GET /alternative-investments/hedge-funds` — 對沖基金持倉與 NAV
- `GET /alternative-investments/liquidity-analysis` — 流動性分析

## Acceptance Criteria
- [ ] 可輸入私募基金資料（承諾資本、實際投資、估值）
- [ ] REITs 價格同步（yfinance 上市 REITs）
- [ ] 流動性分析顯示（流動/半流動/閉鎖）
- [ ] 另類資產總配置百分比
- [ ] 單元測試覆蓋
