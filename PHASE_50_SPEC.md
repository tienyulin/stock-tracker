# Phase 50: AI-Powered Financial Coach & Retirement Readiness — SPEC

## Overview
提供 AI 個人財務教練功能，結合退休規劃 Readiness 評估，透過對話式互動引導用戶達成財務目標。

## Current State
- ✅ Phase 30 AI Agent 框架已完成（AgentOrchestrationService, GoalMonitoringService）
- ✅ RetirementGapResult schema 存在
- ✅ GoalMonitoringService.calculate_retirement_gap() 存在
- ⚠️ 缺乏對話式 Financial Coach 介面
- ⚠️ 缺乏 Retirement Readiness 評估儀表板

## Target State
- 🔄 FinancialCoachAgent — 對話式 AI 教練，根據用戶財務狀況提供個人化建議
- 🔄 RetirementReadinessService — 退休準備度評估與缺口分析
- 🔄 FinancialCoachAPI — REST API 端點供前端调用
- 🔄 CoachMessage schema — 教練對話訊息結構

## Architecture

### Components
1. **FinancialCoachAgent** (app/services/financial_coach_agent.py)
   - 繼承現有 AgentOrchestrationService 框架
   - 提供個人化財務建議（基於用戶 profile、目標、投資組合）
   - 退休規劃指導
   - 教育性財務知識問答

2. **RetirementReadinessService** (app/services/retirement_readiness_service.py)
   - 整合現有 GoalMonitoringService.calculate_retirement_gap()
   - 提供退休準備度評分（0-100）
   - 根據年齡、收入、風險偏好給出改善建議

3. **FinancialCoachAPI** (app/api/v1/financial_coach.py)
   - POST /coach/message — 發送教練訊息
   - GET /coach/conversation — 取得對話歷史
   - GET /coach/retirement-readiness — 取得退休準備度評估

### Data Flow
```
User → FinancialCoachAPI → FinancialCoachAgent
                              ↓
                         GoalMonitoringService
                         RetirementReadinessService
                              ↓
                         AgentRecommendation → User
```

## Acceptance Criteria
- [ ] FinancialCoachAgent 可根據用戶財務 Profile 提供建議
- [ ] RetirementReadinessService 回傳 0-100 評分
- [ ] API 端點已註冊並可正常呼叫
- [ ] 單元測試覆蓋新服務

## Out of Scope
- 即時對話（WebSocket）— 未來 Phase
- 多語言教練語音 — 未來 Phase
