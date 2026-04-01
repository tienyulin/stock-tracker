# Stock Tracker Project - Task Board

**Last Updated:** 2026-03-31
**Status:** Phase 1 ✅ → Phase 2 ✅ → Phase 3 ✅ → Phase 4 ✅ → **Phase 5 🚧 IN PROGRESS**
**Project Lead:** Hermes (CSO/PM)
**Tech Lead:** Athena (CTO)

---

## 📌 Current Live URLs

| Service | URL | Status |
|---------|-----|--------|
| Frontend (Vercel) | https://stock-tracker-xi-one.vercel.app | ✅ Deployed |
| Frontend (Custom) | https://stock.tienyulin.com | ✅ DNS OK |
| Backend API | https://stock-tracker-api-5ht7.onrender.com | ✅ Deployed |
| API Docs | https://stock-tracker-api-5ht7.onrender.com/docs | ✅ |

---

## ✅ Completed Phases

### Phase 1 - MVP
- Basic stock price display
- Docker Compose setup
- API integration

### Phase 2 - Core Features
- Technical Indicators (RSI, MACD, SMA, EMA)
- Watchlist with multi-list support
- Price Alerts with notifications
- Stock Chart (1mo history)
- Market Overview (S&P 500, Nasdaq, Dow Jones, 10Y Treasury)
- Search Autocomplete
- Mobile Responsive

### Phase 3 - Deployment & Growth

| PR | Feature | Status |
|----|---------|--------|
| #53 | Vercel SPA Routing Fix | ✅ Merged |
| #54 | TWSE 台灣股票支援 | ✅ Merged |
| #56 | JWT User Authentication | ✅ Merged |
| #58 | WebSocket Real-time Price Updates | ✅ Merged |
| #59 | Fix RSI undefined error | ✅ Merged |
| #60 | Vercel Redeploy Trigger | ✅ Merged |

---

## 🐛 Open Issues

| # | Title | Priority | Status |
|---|-------|----------|--------|
| #83 | Dashboard 技術指標（RSI/SMA/EMA/MACD）全部 N/A | 🔴 High | 🆕 New |
| #84 | Dashboard Market Overview（S&P 500/NASDAQ/Dow Jones/10Y）全部 N/A | 🔴 High | 🆕 New |
| #49 | DNS: stock.tienyulin.com not pointing to correct hosts | High | 🔴 Tony's task |
| #20 | Implement Technical Indicators (RSI, MACD, MA) | - | ❌ Stale (already done) |

---

## 📋 Phase 4 - Current Sprint

**Status:** 🚧 In Progress
**Start:** 2026-04-01
**PM:** Hermes | **Tech Lead:** Athena

### 🎯 Sprint Goals
1. 驗證所有功能在正式環境正常運作
2. 用戶登入/登出流程完整化
3. 為未來 LINE 通知整合做準備

---

### P0 — 現有功能驗證

| # | Task | Owner | Status |
|---|------|-------|--------|
| 4-01 | 測試所有 API endpoint（watchlists CRUD, alerts CRUD, auth） | Athena | 🔄 In Progress |
| 4-02 | 前端 https://stock.tienyulin.com 全功能驗證 | Athena | ⏳ Pending |
| 4-03 | 確認 Render auto-deploy 設定正確（吃 main branch） | Athena | ⏳ Pending |

---

### P1 — 用戶功能完整化

| # | Task | Owner | Status |
|---|------|-------|--------|
| 4-04 | 登入/登出 UI 流程完整（demo user 能正常操作） | Athena | ⏳ Pending |
| 4-05 | 錯誤處理優化（DB 失敗、網路錯誤 graceful handling） | Athena | ⏳ Pending |

---

### P1 — LINE 通知整合（規劃中）

| # | Task | Owner | Status |
|---|------|-------|--------|
| 4-06 | LINE Messaging API 研究與評估 | Athena | ⏳ Pending |
| 4-07 | LINE token 設定 UI 設計 | Athena | ⏳ Pending |
| 4-08 | Alert 觸發時發送 LINE 通知實作 | Athena | ⏳ Pending |

---

### P2 — Mobile PWA

| # | Task | Owner | Status |
|---|------|-------|--------|
| 4-09 | Service Worker 設定 | Athena | ⏳ Pending |
| 4-10 | Offline support | Athena | ⏳ Pending |

---

## 📋 Phase 4 - Next Steps (Proposed)

| Priority | Feature | Notes |
|----------|---------|-------|
| P0 | Verify all features work on live deployment | Testing phase |
| P1 | User Auth complete flow (login/logout UI) | Post-mvp |
| P1 | LINE alert integration | Notify via LINE |
| P2 | Mobile app (PWA first) | |

---

## 🔗 Deployment Info

- **Frontend:** Vercel (GitHub Student Pack)
- **Backend:** Render.com free tier
- **Database:** Neon PostgreSQL
- **Redis:** Upstash

---

## 🚧 Phase 5 - Signal Engine & Smart Recommendations

**Status:** 🚧 In Progress
**Start:** 2026-04-02
**PM:** Hermes | **Tech Lead:** Athena

### 🎯 Sprint Goals
1. 自動化股票評估系統（好/不好）
2. 信心度顯示
3. 詳細原因說明（哪個指標導致評估）
4. 教育性內容（每個指標代表什麼意義）

---

### P0 — Signal Engine API

| # | Task | Owner | Status |
|---|------|-------|--------|
| 5-01 | Signal Engine API（後端訊號計算服務） | Athena | ✅ Done |
| 5-02 | 評估演算法設計（基於技術指標的買賣信號） | Athena | ✅ Done |

---

### P1 — Frontend Signal Display

| # | Task | Owner | Status |
|---|------|-------|--------|
| 5-03 | Dashboard 快速評估顯示（好/不好/理由） | Athena | ✅ Done |
| 5-04 | 信心度視覺化（百分比或等級） | Athena | ✅ Done |
| 5-05 | 指標詳解（每個指標的意義說明） | Athena | ✅ Done |

---

### P2 — 進階功能

| # | Task | Owner | Status |
|---|------|-------|--------|
| 5-06 | 歷史信號追蹤 | Athena | ✅ Done |
| 5-07 | 個人化推薦（基於用戶投資偏好） | Athena | ⏳ Pending |

---

## 📐 Development Rules

1. **Branch Strategy:** `feature/` → `develop` → `main`
2. **PR Requirements:** CI/test, CI/lint, Code Quality checks
3. **Workflow:** Issue → Branch → TDD → Implement → Test → PR → Review → Merge
