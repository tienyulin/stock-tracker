# Phase 49: Multi-Generational Wealth Transfer & Dynasty Trust — SPEC

## Overview
幫助用戶規劃跨代財富轉移，包括遺產信託、教育基金和家族財富延續策略。

## Current State
- ⚠️ 缺乏教育基金規劃功能
- ⚠️ 缺乏 Trust 資料管理
- ⚠️ 缺乏跨代時間線功能
- ⚠️ 缺乏家族憲法/投資政策說明書功能

## Target State
- 🔄 EducationFundService — 529 計劃追蹤、教育費用預估、儲蓄進度
- 🔄 TrustManagementService — Trust 帳戶追蹤、受益人分配、條款提醒
- 🔄 WealthTransferTimelineService — 家族里程碑、遺產分配模擬、稅務影響
- 🔄 FamilyConstitutionService — 投資政策說明書、家族價值觀、傳承教育
- 🔄 API 端點與前端整合

## Architecture

### Data Models
1. **EducationFund** — 529 計劃帳戶
2. **TrustAccount** — Trust 帳戶
3. **Beneficiary** — 受益人
4. **WealthTransferTimeline** — 跨代時間線事件
5. **FamilyConstitution** — 家族憲法文件

### Services
1. **EducationFundService** — 教育基金進度追蹤
2. **TrustManagementService** — Trust 全生命週期管理
3. **WealthTransferTimelineService** — 時間線規劃與模擬
4. **FamilyConstitutionService** — 家族投資政策管理

### API Endpoints
- /education-fund/* — 教育基金 CRUD
- /trust/* — Trust 管理
- /wealth-timeline/* — 時間線
- /family-constitution/* — 家族憲法

## Acceptance Criteria
- [ ] 教育基金進度顯示
- [ ] Trust 資料管理正常
- [ ] 時間線規劃可用
- [ ] 單元測試覆蓋
