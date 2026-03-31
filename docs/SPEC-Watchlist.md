# SPEC: Watchlist Feature

**Version:** 0.1 (Draft)
**Author:** Hermes (CSO/PM)
**Date:** 2026-03-30
**Status:** COMPLETE
**Owner:** Hermes (spec) + Athena (development)

---

## 1. Overview

**What:** Allow users to save, manage, and quickly access a personal list of stocks they want to track.

**Why:** Users need persistent, personalized views of their关注 stocks without searching every time.

**User:** Retail investor in Taiwan market

---

## 2. User Stories

### US-1: Add Stock to Watchlist
**As a** logged-in user  
**I want to** add a stock by symbol (e.g., 2330.TW)  
**So that** I can track it on my dashboard

**Acceptance:**
- Search by symbol or company name
- Add via button on stock detail page
- Add via search bar
- Toast notification confirms "Added to watchlist"
- Duplicate add shows friendly error "Already in watchlist"

### US-2: Remove Stock from Watchlist
**As a** logged-in user  
**I want to** remove a stock from my watchlist  
**So that** I can keep the list relevant

**Acceptance:**
- Swipe-to-delete on mobile, X button on desktop
- Confirmation dialog: "Remove 2330 from watchlist?"
- Undo available for 5 seconds after removal

### US-3: View Watchlist on Dashboard
**As a** logged-in user  
**I want to** see my watchlist on the main dashboard  
**So that** I get a quick overview of my tracked stocks

**Acceptance:**
- Watchlist appears as a card/section on dashboard
- Shows: symbol, current price, change %, mini sparkline (7-day)
- Sorted by user-defined order (drag & drop)
- Empty state: "Your watchlist is empty. Add stocks to get started."

### US-4: Persist Watchlist Across Sessions
**As a** logged-in user  
**I want to** see my watchlist when I return  
**So that** I don't lose my selections

**Acceptance:**
- Stored in PostgreSQL (user_id, symbol, position, created_at)
- Synced to Redis for fast reads
- Available on any device when logged in

### US-5: Reorder Watchlist
**As a** logged-in user  
**I want to** drag and drop to reorder my watchlist  
**So that** most important stocks are at the top

**Acceptance:**
- Drag handle on each row
- Order saved immediately
- Smooth animation during drag

---

## 3. Technical Approach

### Backend (FastAPI)

**Database Schema:**
```sql
CREATE TABLE watchlist (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    position INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, symbol)
);

CREATE INDEX idx_watchlist_user ON watchlist(user_id);
```

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/watchlist` | Get user's watchlist (ordered by position) |
| POST | `/api/watchlist` | Add stock to watchlist `{ "symbol": "2330.TW" }` |
| DELETE | `/api/watchlist/{symbol}` | Remove stock from watchlist |
| PATCH | `/api/watchlist/reorder` | Reorder watchlist `{ "symbols": ["2330.TW", "2317.TW", ...] }` |

**Response Format:**
```json
{
  "watchlist": [
    {
      "symbol": "2330.TW",
      "name": "台積電",
      "price": 875.0,
      "change_percent": 2.34,
      "position": 0
    }
  ]
}
```

### Frontend (React)

**Components:**
- `WatchlistCard` — displays watchlist on dashboard
- `WatchlistSearch` — search/add stocks
- `WatchlistItem` — individual row with drag handle
- `WatchlistEmpty` — empty state CTA

**State Management:**
- React Query for server state
- Optimistic updates for add/remove
- Local drag state for reordering

---

## 4. Design Notes

- **Desktop:** Watchlist as right sidebar or bottom panel on dashboard
- **Mobile:** Horizontal scrolling chips at top, full list on tap
- **Colors:** Follow existing dashboard palette
- **Loading:** Skeleton shimmer while fetching

---

## 5. Out of Scope (MVP)

- Watchlist sharing (Phase 4)
- Multiple watchlists / watchlist groups
- Price alerts integration (separate feature)
- Export watchlist

---

## 6. Dependencies

- Phase 1 auth system (user accounts)
- Stock price API (existing)
- Redis for caching

---

## 7. Priority

**P0** — MVP watchlist (US-1, US-2, US-3, US-4)
**P1** — Reorder (US-5)

---

**Note:** This feature has been implemented by Athena (PR #10 merged 2026-03-29).
This spec serves as documentation and validation.
