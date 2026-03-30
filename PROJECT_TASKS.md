# Stock Tracker Project - Task Board

**Last Updated:** 2026-03-30
**Status:** Phase 1 ✅ → Phase 2 ✅ → **Phase 3 Active (Deployment)**
**Project Lead:** Hermes (CSO/PM)
**Tech Lead:** Athena (CTO)

---

## Project Overview

A web-based stock tracking system for Taiwan market with:
- Real-time price tracking
- Technical analysis indicators (RSI, MACD, MA)
- Personalized watchlist with multi-list support
- Price alert notifications with reset capability
- Market overview (S&P 500, Nasdaq, Dow Jones, Treasury)
- Interactive stock charts

**Tech Stack:**
- Frontend: React + TypeScript + Vite
- Backend: FastAPI (Python)
- Database: PostgreSQL (Neon free tier)
- Redis: Upstash (free tier)
- Deployment: Vercel (Frontend) + Render (Backend)

**Repo:** https://github.com/tienyulin/stock-tracker

---

## ✅ Phase 1 - MVP Completed

- [x] Basic stock price display
- [x] Docker Compose setup (Backend/Frontend/PostgreSQL/Redis)
- [x] API integration and testing
- [x] Development workflow rules documented

---

## ✅ Phase 2 - Features Completed

### Task 1: Technical Indicators
**Status:** ✅ COMPLETED (2026-03-30)
**PR:** #22

**Implementation:**
- Backend: `app/services/indicators_service.py` - RSI, MACD, SMA, EMA calculations
- API: `GET /api/v1/stocks/{symbol}/indicators`
- Frontend: `StockIndicators.tsx` component in StockSearch page
- Tests: `tests/services/test_indicators_service.py`

---

### Task 2: Watchlist Feature
**Status:** ✅ COMPLETED (2026-03-29)
**PR:** #10

**Implementation:**
- Backend: `app/api/v1/watchlists.py`, `app/services/watchlist_service.py`
- Models: `Watchlist`, `WatchlistItem` with PostgreSQL
- Frontend: `Watchlist.tsx` with sort, create, parallel loading

---

### Task 3: Price Alerts
**Status:** ✅ COMPLETED (2026-03-29)
**PR:** #11

**Implementation:**
- Backend: `app/api/v1/alerts.py`, `app/services/alert_service.py`
- Models: `Alert` with condition types (above/below/change_pct)
- Frontend: `Alerts.tsx` with filter tabs, notifications, reset

---

## ✅ Phase 2 Enhancements (Completed Today)

| Feature | PR | Description |
|---------|-----|-------------|
| Stock Chart | #35 | Line chart with 1mo history (recharts) |
| Market Overview | #36 | S&P 500, Nasdaq, Dow Jones, 10Y Treasury |
| Alerts Enhancement | #37 | Filter tabs, toast notifications, reset button |
| Watchlist Enhancement | #38 | Sort by symbol/price, create list, parallel loading |
| Mobile Responsive | #39 | Responsive navbar, stock grids, active link highlight |
| Python 3.9 Fix | #33 | `from __future__ import annotations` for union types |
| Structured Logging | #34 | JSON-like logging format + enhanced /health |
| Plugin Fix | #32 | `@vitejs/plugin-react` 5.x for vite 8 |
| Price Change + Skeletons | #43 | Real-time price change display + loading skeletons |
| Search Autocomplete | #41 | Search with autocomplete + popular stocks suggestions |
| ErrorBoundary | #42 | React ErrorBoundary to prevent page crashes |

**develop branch: CLEAN ✅ | CI: ALL GREEN ✅** |

---

## 🚀 Phase 3 - Deployment (Active)

**Status:** Awaiting Tony's deployment account setup

**Decision (Tony approved):**
- Deploy externally (public URL, accessible beyond localhost)
- 100% free — no paid components whatsoever
- Internal team testing only — no public promotion
- Domain: **tienyulin.com** (Tony's existing domain)

**Stack (all free + Tony's GitHub Student Pack):**
- Frontend: **Vercel Pro** ✅ (GitHub Student Pack — unlimited bandwidth)
- Backend: **Render.com** (free tier, FastAPI compatible)
- Database: **Neon** (free PostgreSQL tier)
- Redis: **Upstash** (free serverless Redis)

**Files Ready for Deployment:**
- ✅ `DEPLOY.md` - Complete deployment guide
- ✅ `frontend/vercel.json` - Vercel config (SIN1 region)
- ✅ `.env.example` - Environment variable template
- ✅ `render.yaml` - Render Blueprint
- ✅ FastAPI CORS middleware configured

**Pending (needs Tony's accounts):**
- [ ] Tony: Create Neon PostgreSQL → share DATABASE_URL
- [ ] Tony: Create Upstash Redis → share REDIS_URL
- [ ] Tony: Connect Render to GitHub repo → deploy backend
- [ ] Tony: Connect Vercel to GitHub repo → deploy frontend
- [ ] Tony: Configure DNS for tienyulin.com

---

## 📋 Future Phases (Backlog)

| Priority | Feature | Notes |
|----------|---------|-------|
| High | User authentication | JWT or Auth0 |
| Medium | Real-time price updates | WebSocket |
| Medium | Taiwan market support | TWSE stocks |
| Low | Mobile app | PWA first |
| Low | LINE integration | Alert notifications |

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

## 📊 CI/CD Status

**All 61 tests passing ✅**
**All CI checks passing ✅**

| Check | Status |
|-------|--------|
| CI/test | ✅ |
| CI/lint | ✅ |
| Code Quality/format-check | ✅ |
| Code Quality/type-check | ✅ |
| Security/security-scan | ✅ |
| Security/dependency-check | ✅ |

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
│   │   └── services/       # API client
│   └── tests/
├── docker-compose.yml
├── DEPLOY.md
└── .github/workflows/
```

---

## 🔗 Links

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- GitHub Repo: https://github.com/tienyulin/stock-tracker

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

**Decision (Tony approved):**
- Deploy externally (public URL, accessible beyond localhost)
- 100% free — no paid components whatsoever
- Internal team testing only — no public promotion
- URL shared only within Pantheon team

**Stack (all free + Tony's GitHub Student Pack):**
- Frontend: **Vercel Pro** ✅ (GitHub Student Pack — unlimited bandwidth, no hobby limits)
- Backend: Render.com (free tier, FastAPI compatible)
- Database: Supabase free PostgreSQL OR Neon free tier
- Redis: Upstash free (serverless Redis)
- Domain: **tienyulin.com** ✅ (Tony's existing domain)

**Domain Plan:**
- `stock-tracker.tienyulin.com` → Frontend (Vercel)
- `api.stock-tracker.tienyulin.com` → Backend API (Render)

**Subtasks:**
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
