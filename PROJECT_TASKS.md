# Stock Tracker Project - Task Board

**Last Updated:** 2026-03-29
**Status:** Phase 1 Complete → Phase 2 In Progress
**Project Lead:** Hermes (CSO/PM)
**Tech Lead:** Athena (CTO)

---

## 📋 Project Overview

A web-based stock tracking system for Taiwan market with:
- Real-time price tracking
- Technical analysis indicators
- Personalized watchlist
- Price alert notifications

**Tech Stack:**
- Frontend: React
- Backend: FastAPI
- Database: PostgreSQL + Redis
- Deployment: Docker Compose

**Repo:** (Ask Athena for GitHub URL)
**Dev URL:** http://localhost:3000 (Frontend) | http://localhost:8000 (Backend)

---

## ✅ Phase 1 - MVP Completed (Issues #1-5)

- [x] Basic stock price display
- [x] Docker Compose setup (Backend/Frontend/PostgreSQL/Redis)
- [x] API integration and testing
- [x] Development workflow rules documented

---

## 🔄 Phase 2 - Technical & Features (Current)

### Task 1: Technical Indicators
**Status:** CI PASSED - MERGE BLOCKED (GitHub branch protection sync issue)
**Issue:** #20 (Implement Technical Indicators)
**PR:** #22 (awaiting merge - CLI blocked by branch protection)
**Branch:** feature/technical-indicators (from develop)
**Description:** Implement RSI, MACD, MA calculations for Taiwan stocks
**Acceptance Criteria:**
- [x] RSI calculation with period=14
- [x] MACD calculation (12, 26, 9 standard)
- [x] MA calculation (5, 10, 20, 60 day moving averages)
- [x] API endpoint to fetch indicators for any stock symbol
- [x] Frontend chart display

**Subtasks:**
- [ ] Create Python utility for RSI formula
- [ ] Create Python utility for MACD formula
- [ ] Create Python utility for MA calculations
- [ ] Create FastAPI endpoint `/api/indicators/{symbol}`
- [ ] Add frontend component to display indicators
- [ ] Add to stock detail page
- [ ] Write unit tests
- [ ] Test with real stock data
- [ ] Merge to develop

**Report:** After each subtask completion

---

### Task 2: Watchlist Feature
**Status:** PENDING
**Issue:** #7
**Branch:** feature/watchlist
**Description:** Allow users to save and manage personal stock watchlist
**Acceptance Criteria:**
- User can add/remove stocks from watchlist
- Watchlist persists across sessions
- Quick access from main dashboard
- Support for Taiwan stock format (e.g., 2330.TW)

---

### Task 3: Price Alerts
**Status:** PENDING
**Issue:** #8
**Branch:** feature/price-alerts
**Description:** Set price conditions to trigger notifications
**Acceptance Criteria:**
- User sets alert conditions (above/below price)
- Backend checks prices periodically (or on-demand)
- Notification sent when condition met
- Alert management UI (create/delete/view)

---

## 📐 Development Rules (Team Protocol)

1. **Branch Strategy:**
   - All work from `develop` branch
   - Create feature branch: `feature/[feature-name]`
   - Merge back to `develop` when complete

2. **Workflow:**
   - Open Issue (English) → Add to Kanban → Branch → Implement → Test → Merge → Report

3. **Naming Convention:**
   - Branch: `feature/`, `bugfix/`, `hotfix/`
   - Commit: descriptive, English, imperative mood

4. **Reporting:**
   - Report after each subtask completion
   - Report any blockers immediately
   - Daily summary at 20:00 (Asia/Taipei)

---

## 📁 File Locations

- **Project Workspace:** `/Users/tienyu/Project/agent-workspace`
- **Shared Tasks:** This file
- **OpenClaw Workspaces:** `~/.openclaw/workspace-{agent}`

---

## 🔗 Links

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- GitHub Kanban: (Ask Athena)
