# Phase 20: Monte Carlo Retirement Projection — SPEC

## Overview
提供 Monte Carlo 模擬引擎，幫助用戶評估退休規劃的成功率，透過 1,000-5,000 次隨機模擬生成未來投資組合價值的信心區間。

## Current State
- ✅ Phase 19 AI Portfolio Assistant 已完成
- ✅ GoalMonitoringService.calculate_retirement_gap() 存在
- ✅ PersonalFinancialProfile schema 存在
- ❌ 無 Monte Carlo 模擬引擎
- ❌ 無 retirement projection API
- ❌ 無視覺化儀表板

## Target State
- 🔄 MonteCarloSimulationService — 非同步 Monte Carlo 模擬引擎
- 🔄 RetirementProjectionAPI — REST API 端點
- 🔄 SimulationResult schema — 模擬結果結構
- 🔄 Frontend — Fan chart 視覺化

## Architecture

### Components

#### 1. MonteCarloSimulationService (app/services/monte_carlo_service.py)
- 繼承 AsyncBaseService 模式
- 支援 3 種風險配置：conservative / moderate / aggressive
- 預設 1,000 次模擬，最高 5,000 次
- 歷史參數：
  - Equity: ~7% real return, 15% std dev
  - Bonds: ~3% real return, 5% std dev
  - Inflation: ~2.5% annually
- 非同步執行，結果存入資料庫
- 輸出：percentile outcomes (10th, 25th, 50th, 75th, 90th)

#### 2. RetirementProjectionAPI (app/api/v1/retirement_projection.py)
- POST /retirement/projection/run — 觸發新模擬
- GET /retirement/projection/{id} — 取得模擬結果
- GET /retirement/projection/history — 用戶歷史模擬
- DELETE /retirement/projection/{id} — 刪除模擬

#### 3. Data Models
- SimulationRun: id, user_id, risk_profile, inputs snapshot, created_at, status
- SimulationResult: id, run_id, percentile, portfolio_values_by_year

### API Request/Response

**POST /api/v1/retirement/projection/run**
```json
{
  "current_age": 35,
  "retirement_age": 65,
  "current_portfolio_value": 500000,
  "monthly_contribution": 2000,
  "desired_monthly_retirement_income": 5000,
  "risk_profile": "moderate",
  "num_simulations": 1000
}
```

**Response:**
```json
{
  "run_id": "uuid",
  "status": "pending",
  "estimated_completion_seconds": 30
}
```

**GET /api/v1/retirement/projection/{run_id}**
```json
{
  "run_id": "uuid",
  "status": "completed",
  "success_rate": 0.87,
  "percentiles": {
    "p10": [500000, 480000, ...],
    "p25": [500000, 520000, ...],
    "p50": [500000, 580000, ...],
    "p75": [500000, 650000, ...],
    "p90": [500000, 720000, ...]
  },
  "years_until_depletion_worst_case": 42,
  "median_portfolio_at_retirement": 2400000
}
```

## Acceptance Criteria
- [ ] MonteCarloSimulationService 可執行 1,000+ 次模擬
- [ ] 支援 conservative/moderate/aggressive 三種風險配置
- [ ] 非同步執行，結果入庫
- [ ] API 端點已註冊並可正常呼叫
- [ ] 單元測試覆蓋模擬引擎
- [ ] Frontend fan chart 顯示信心區間

## Out of Scope
- 即時 WebSocket 推送模擬進度
- 與真實市場資料連動（使用靜態歷史參數）
- Social sharing of results

## Tech Stack
- Backend: Python FastAPI, numpy/scipy for simulation
- Frontend: React + Recharts (fan chart)
- Storage: PostgreSQL JSONB for simulation results
