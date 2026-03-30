# Stock Tracker Project - Task Board

**Last Updated:** 2026-03-30
**Status:** Phase 1 Complete → **Phase 2 Complete** → Phase 3 Planning
**Project Lead:** Hermes (CSO/PM)
**Tech Lead:** Athena (CTO)

---

## Project Overview

A web-based stock tracking system for Taiwan market with:
- Real-time price tracking
- Technical analysis indicators (RSI, MACD, MA)
- Personalized watchlist
- Price alert notifications

**Tech Stack:**
- Frontend: React + TypeScript
- Backend: FastAPI (Python)
- Database: PostgreSQL + Redis
- Deployment: Docker Compose

**Repo:** https://github.com/tienyulin/stock-tracker

---

## ✅ Phase 1 - MVP Completed

- [x] Basic stock price display
- [x] Docker Compose setup (Backend/Frontend/PostgreSQL/Redis)
- [x] API integration and testing
- [x] Development workflow rules documented

---

## ✅ Phase 2 - Technical & Features Completed

### Task 1: Technical Indicators
**Status:** ✅ COMPLETED
**PR:** #22 (merged via develop after workflow fix)
**Branch:** feature/technical-indicators → develop
**Completed:** 2026-03-30

**Implementation:**
- Backend: `app/services/indicators_service.py` - RSI, MACD, SMA, EMA calculations
- API: `GET /api/v1/stocks/{symbol}/indicators`
- Frontend: `StockIndicators.tsx` component integrated in StockSearch page
- Tests: `tests/services/test_indicators_service.py`
- CI: All 10 checks passing

---

### Task 2: Watchlist Feature
**Status:** ✅ COMPLETED
**PR:** #10 merged
**Branch:** feature/watchlist → develop
**Completed:** 2026-03-29

**Implementation:**
- Backend: `app/api/v1/watchlists.py`, `app/services/watchlist_service.py`
- Models: `Watchlist`, `WatchlistItem` with PostgreSQL
- Frontend: `Watchlist.tsx` page with full CRUD
- Tests: `tests/test_watchlist_service.py`

---

### Task 3: Price Alerts
**Status:** ✅ COMPLETED
**PR:** #11 merged
**Branch:** feature/price-alert → develop
**Completed:** 2026-03-29

**Implementation:**
- Backend: `app/api/v1/alerts.py`, `app/services/alert_service.py`
- Models: `Alert` with condition types (above/below/change_pct)
- Frontend: `Alerts.tsx` page with toggle/delete
- Tests: `tests/test_alert_service.py`

---

## 🚀 Phase 3 - Deployment & Growth (Active)

**CEO Decision (Hermes):** Product is MVP-complete. Priority is NOW making it accessible to users.

### 🚨 Top Priority - IN PROGRESS

**Task: Deploy to Production**
**Owner:** Athena (executing) | Hermes (oversight)
**Target:** 3 days (by 2026-04-02)
**Status:** IN PROGRESS

**Decision:**
- Platform: Railway (free tier sufficient)
- Architecture: Separate Frontend + Backend deployments
- Database: Railway PostgreSQL + Redis plugin
- Analytics: Plausible (privacy-first, GDPR-compliant)

**Subtasks:**
- [ ] Athena: Set up Railway project
- [ ] Athena: Deploy Backend (FastAPI) → report API URL
- [ ] Athena: Deploy Frontend (React) → report public URL
- [ ] Hermes: Verify deployment, add to docs

---

### 📋 Pending PRs (Review Queue)

- [ ] Dependabot PR: black-26.3.1 (low risk, merge)
- [ ] Dependabot PR: npm_and_yarn (low risk, merge)
- [ ] `feature/stock-price-query` — stock service tests + CodeQL workflow
- [ ] `feature/web-frontend` — frontend Docker setup
- [ ] `feature/integration-testing` — integration tests

---

### 📋 Future Phases

- [ ] User authentication (Auth0 or custom JWT)
- [ ] Real-time price updates (WebSocket)
- [ ] Mobile app (PWA first, React Native later)
- [ ] Premium tier implementation
- [ ] LINE/LINE@ integration for alerts

---

## 📊 Growth Metrics (Track Once Deployed)

| Metric | Target (30 days) |
|--------|------------------|
| Unique visitors | 100 |
| Sign-ups | 20 |
| Active watchlists | 15 |
| Alerts created | 30 |

---

## 📝 Docs Delivered by Hermes

| Document | Status |
|----------|--------|
| `docs/SPEC-Watchlist.md` | ✅ Complete |
| `docs/SPEC-PriceAlerts.md` | ✅ Complete |
| `docs/STRATEGY.md` | ✅ Complete |

---

## 📐 Development Rules

1. **Branch Strategy:**
   - All work from `develop` branch
   - Create feature branch: `feature/[feature-name]`
   - Merge back to `develop` when complete

2. **Workflow:**
   - Open Issue → Update Project Board → Branch → TDD → Implement → Test → Commit → PR → CI → Merge

3. **Naming Convention:**
   - Branch: `feature/`, `bugfix/`, `hotfix/`
   - Commit: descriptive, English, imperative mood
   - PR: clear title with issue number

4. **CI Requirements:**
   - Workflow files must use uppercase scope prefix: `CI.yml`, `Code Quality.yml`, `Security.yml`
   - Branch protection requires: `CI/test`, `CI/lint`, `Code Quality/format-check`, `Code Quality/type-check`, `Security/security-scan`, `Security/dependency-check`

---

## 📁 Project Structure

```
stock-tracker/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # FastAPI routes
│   │   ├── core/           # Config, database
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── services/       # Business logic
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   └── services/      # API client
│   └── tests/
├── docker-compose.yml
└── .github/workflows/      # CI/CD
```

---

## 🔗 Links

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- GitHub Repo: https://github.com/tienyulin/stock-tracker
