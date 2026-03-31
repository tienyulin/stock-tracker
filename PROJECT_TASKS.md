# Stock Tracker Project - Task Board

**Last Updated:** 2026-03-31
**Status:** Phase 1 ✅ → Phase 2 ✅ → **Phase 3 ✅ DEPLOYED**
**Project Lead:** Hermes (CSO/PM)
**Tech Lead:** Athena (CTO)

---

## 📌 Current Live URLs

| Service | URL | Status |
|---------|-----|--------|
| Frontend | https://frontend-rouge-one-20.vercel.app | ✅ Deployed |
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
| #49 | DNS: stock.tienyulin.com not pointing to correct hosts | High | 🔴 Tony's task |
| #20 | Implement Technical Indicators (RSI, MACD, MA) | - | ❌ Stale (already done) |

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

## 📐 Development Rules

1. **Branch Strategy:** `feature/` → `develop` → `main`
2. **PR Requirements:** CI/test, CI/lint, Code Quality checks
3. **Workflow:** Issue → Branch → TDD → Implement → Test → PR → Review → Merge
