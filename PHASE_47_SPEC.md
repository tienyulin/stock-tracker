# Phase 47: Tax Optimization & Capital Gains Management — SPEC

## Overview
提供資本利得管理與稅務優化建議，幫助用戶最大化税後投資回報。

## Current State
- ✅ TaxReportService — 稅務報告與資本利得計算（已存在）
- ✅ Wash sale 追蹤（已存在）
- ✅ IRS Form 8949 生成（已存在）
- ⚠️ 缺乏稅務優化建議功能
- ⚠️ 缺乏資本利得預測功能
- ⚠️ 缺乏帳戶配置優化建議

## Target State
- 🔄 TaxOptimizationService — 稅務優化策略建議
- 🔄 CapitalGainsProjectionService — 未實現/已實現利得預測
- 🔄 AssetLocationService — 帳戶類型資產配置優化（應稅/退休帳戶）
- 🔄 TaxEfficientWithdrawalService — 稅務高效提款策略
- 🔄 API 端點整合

## Architecture

### New Services
1. **TaxOptimizationService** — 分析投資組合找出節稅機會
   - 呆滯虧損識別（Loss Harvesting Candidates）
   - 高 turnover 持倉預警
   - 持有期最佳化建議
   
2. **CapitalGainsProjectionService** — 預測未實現/已實現資本利得
   - Unrealized gains by position
   - Projected short-term vs long-term at year end
   - Tax liability estimates
   
3. **AssetLocationService** — 根據帳戶類型優化資產配置
   - 應稅帳戶（Taxable）：放置 tax-efficient assets（個股、ETF）
   - 稅務優惠帳戶（Tax-Advantaged）：放置 tax-inefficient assets（高收益債）
   -roth IRA vs Traditional IRA vs 401k 配置建議
   
4. **TaxEfficientWithdrawalService** — 退休提款順序優化
   - RMD 計算
   - 順序：Roth → 應稅 → Traditional IRA/401k
   - 稅務影響模擬

### API Endpoints
- `GET /tax-optimization/summary` — 稅務優化概覽
- `GET /tax-optimization/loss-harvesting` — 可補虧損標的清單
- `GET /capital-gains/projection` — 資本利得預測
- `GET /asset-location/recommendations` — 帳戶配置建議
- `GET /withdrawal/strategy` — 提款策略建議

## Acceptance Criteria
- [ ] TaxOptimizationService 正常運作
- [ ] Loss harvesting 機會識別正確
- [ ] 資本利得預測合理
- [ ] 帳戶配置建議符合 Tax-Lot Location Effect 原則
- [ ] 單元測試覆蓋
