# SPEC: User Authentication

**Version:** 0.1 (Draft)
**Author:** Hermes (CSO/PM)
**Date:** 2026-03-30
**Status:** IN PROGRESS
**Owner:** Hermes (spec) + Athena (development)

---

## 1. Overview

**What:** User registration and login system to persist watchlists, alerts, and preferences across devices.

**Why:** Without auth, user data can't persist — no personalized experience, no paid features possible.

**User:** Any visitor who wants to save their watchlist and alerts

---

## 2. User Stories

### US-1: Sign Up
**As a** visitor  
**I want to** create an account with email + password  
**So that** I can access my data from any device

**Acceptance:**
- Email format validation
- Password minimum 8 chars
- Duplicate email shows error "Account already exists"
- Welcome email sent (optional, Phase 2)
- Auto-login after registration

### US-2: Login
**As a** registered user  
**I want to** log in with email + password  
**So that** I can access my watchlist and alerts

**Acceptance:**
- Wrong password shows "Invalid email or password" (no specifics)
- Successful login redirects to dashboard
- "Remember me" checkbox (optional, 30-day session)
- Session persists until logout

### US-3: Logout
**As a** logged-in user  
**I want to** log out  
**So that** no one else can access my account on this device

**Acceptance:**
- Single click logout
- Redirect to home page
- Session invalidated immediately

### US-4: Persistent User Data
**As a** logged-in user  
**I want to** my watchlist and alerts are always available  
**So that** I can track stocks continuously

**Acceptance:**
- Watchlist synced to user account (not device)
- Alerts synced to user account
- Data available on any browser after login

---

## 3. Technical Approach

### Backend (FastAPI)

**Database Schema:**
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

**Password Security:**
- Hash with bcrypt (not plain text, not md5)
- Never log or expose password hash

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Create account `{ "email": "...", "password": "..." }` |
| POST | `/api/auth/login` | Login `{ "email": "...", "password": "..." }` → `{ "token": "..." }` |
| POST | `/api/auth/logout` | Invalidate session |
| GET | `/api/auth/me` | Get current user info |

**JWT Token:**
- Access token stored in httpOnly cookie
- Token expiry: 24 hours (or 30 days if "remember me")
- Refresh mechanism optional for Phase 1

### Frontend (React)

**Pages:**
- `/login` — login form
- `/signup` — registration form
- `/dashboard` — protected route (redirect to login if not authenticated)

**State:**
- Auth state in React Context
- Token in httpOnly cookie (handled by backend)
- Logout clears cookie + redirects

---

## 4. Auth Flow

### Signup
```
User fills form → POST /api/auth/signup
→ Create user in DB (hash password)
→ Set JWT cookie
→ Redirect to dashboard
```

### Login
```
User fills form → POST /api/auth/login
→ Verify password against hash
→ Set JWT cookie
→ Redirect to dashboard
```

### Protected Route
```
User visits /dashboard
→ Check JWT cookie
→ Valid? Show dashboard
→ Invalid/missing? Redirect to /login
```

---

## 5. Out of Scope (Phase 1)

- Social login (Google, LINE)
- Password reset / forgot password
- Email verification
- Two-factor authentication
- OAuth integration

---

## 6. Dependencies

- bcrypt library for password hashing
- python-jose for JWT
- Existing database schema (users table)

---

## 7. Priority

**P0** — Signup + Login + JWT + Protected routes
**P1** — Logout
**P2** — Remember me, password reset

---

## 8. Implementation Notes

**Security checklist:**
- [ ] Passwords hashed with bcrypt (cost factor 12)
- [ ] JWT in httpOnly cookie (not localStorage)
- [ ] HTTPS only in production
- [ ] Rate limiting on login endpoint (prevent brute force)
- [ ] No token info in error messages
