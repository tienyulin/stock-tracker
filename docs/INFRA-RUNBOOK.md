# Infrastructure Runbook

Standard procedures for deployment, troubleshooting, and common infrastructure tasks.

## Table of Contents

- [Deploy Overview](#deploy-overview)
- [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
- [Backend Deployment (Render)](#backend-deployment-render)
- [Triggering Deploys](#triggering-deploys)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Common Issues](#common-issues)

---

## Deploy Overview

The Stock Tracker project uses two deployment targets:

| Service | Repository | Branch | URL |
|---------|------------|--------|-----|
| Frontend (Vercel) | `frontend/` | `main` | https://stock-tracker-frontend.vercel.app |
| Backend (Render) | `stock-tracker` | `main` | https://stock-tracker-api.onrender.com |

### Deploy Flow

```
develop branch → PR merge → CI passes → Merge to main → Auto-deploy
```

**Note:** Render deploys only trigger when `main` branch is updated.

---

## Frontend Deployment (Vercel)

### Architecture

- Vercel handles frontend builds automatically on push to `main`
- Environment variables configured in Vercel dashboard
- Preview deployments for all PRs

### Deploy Trigger

Frontend auto-deploys when `main` branch is updated:

```bash
git checkout main
git merge develop
git push origin main
```

### Manual Deploy (Vercel CLI)

```bash
npm install -g vercel
cd frontend
vercel --prod
```

### Rollback (Vercel Dashboard)

1. Go to Vercel Dashboard → Deployments
2. Find the last working deployment
3. Click "..." → "Promote to Production"

### Environment Variables (Vercel)

| Variable | Description |
|----------|-------------|
| `VITE_API_TARGET` | Backend API URL (default: http://localhost:8000) |

---

## Backend Deployment (Render)

### Architecture

- Render Blueprint (`render.yaml`) defines the service
- Python 3.12, uvicorn server
- PostgreSQL database (Render managed or external)

### Deploy Trigger

Render deploys **only** when `main` branch is updated via GitHub integration.

### Manual Deploy (Render Dashboard)

1. Go to Render Dashboard → stock-tracker-api
2. Click "Manual Deploy" → "Deploy latest commit"

### Force Deploy via Empty Commit

When you need to trigger a deploy without code changes:

```bash
# For backend (Render)
git commit --allow-empty -m "chore: trigger deploy"
git push origin main

# Or for frontend only (Vercel)
cd frontend
vercel --prod
```

### Environment Variables (Render)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API key |
| `DISCORD_WEBHOOK_URL` | Discord notification webhook |
| `LINE_NOTIFY_TOKEN` | LINE Notify access token |

### Health Check

Backend health endpoint: `GET /health`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "stock-tracker-api"
}
```

---

## Triggering Deploys

### Method 1: Merge to Main (Recommended)

```bash
git checkout main
git merge develop
git push origin main
```

### Method 2: Empty Commit (Force Redeploy)

```bash
# Backend deploy trigger
git commit --allow-empty -m "chore: force deploy"
git push origin main

# Frontend only - Vercel CLI
cd frontend && vercel --prod
```

### Method 3: Manual Deploy (Render Dashboard)

1. Render Dashboard → stock-tracker-api service
2. Manual Deploy → Deploy latest commit

---

## Troubleshooting Guide

### Frontend Issues

#### Build Failures

1. Check Vercel build logs for errors
2. Common causes:
   - Missing environment variables
   - TypeScript compilation errors
   - Missing dependencies in `package.json`

```bash
# Local build test
cd frontend
npm install
npm run build
```

#### Deployment Not Updating

1. Clear Vercel cache: Dashboard → Settings → General → Clear Cache
2. Check if correct branch is connected
3. Verify environment variables are set

#### CORS Errors

If frontend can't reach backend:
1. Check backend `ALLOWED_ORIGINS` setting
2. Verify backend is running and accessible
3. Check browser console for specific CORS error

### Backend Issues

#### Render Deployment Fails

1. Check Render build logs
2. Common causes:
   - Missing environment variables
   - Python version mismatch (needs 3.12)
   - Database connection issues

```bash
# Local test
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Database Connection Issues

1. Verify `DATABASE_URL` is correct
2. Check if database is accessible from Render's network
3. For local testing, ensure PostgreSQL is running

```bash
# Test database connection locally
psql $DATABASE_URL
```

#### API Returns 500 Error

1. Check backend logs in Render dashboard
2. Common causes:
   - External API failure (Yahoo Finance, Alpha Vantage)
   - Database query error
   - Invalid configuration

### CI/CD Issues

#### GitHub Actions Failing

1. Go to Actions tab → Find failing workflow
2. Check job logs for specific error
3. Common fixes:
   - Re-run failed jobs (sometimes transient)
   - Fix lint/test issues locally before pushing

```bash
# Run lint locally
npm run lint        # Frontend
python -m ruff check .  # Backend

# Run tests locally
npm test            # Frontend
pytest              # Backend
```

#### Secrets Not Working

1. Verify secrets are set in GitHub repository settings
2. Secrets need to be recreated if repository was forked
3. Check if secret name matches code references

---

## Common Issues

### "Push empty commit" Not Triggering Deploy

**Problem:** Empty commit doesn't always trigger Render.

**Solution:**
```bash
git commit --allow-empty -m "trigger: force rebuild"
git push origin main
```

If still not working:
1. Check Render dashboard for deployment history
2. Try manual deploy via Render dashboard
3. Verify GitHub integration is still connected

### Vercel Preview Not Working

**Problem:** PR preview deployments not showing.

**Solution:**
1. Check Vercel dashboard for the project
2. Verify GitHub app permissions
3. Check if `vercel.json` is configured correctly

### Environment Variables Not Loading

**Problem:** App can't find environment variables.

**Solution:**

Frontend (Vercel):
```bash
vercel env pull  # Pull environment variables locally
```

Backend (Render):
1. Dashboard → Environment → Add Environment Variable
2. Redeploy after adding

### Database Migration Issues

**Problem:** Schema changes not applied.

**Solution:**
```bash
# Check current migrations
alembic history

# Run pending migrations
alembic upgrade head
```

---

## Emergency Contacts

| Issue | Action |
|-------|--------|
| Frontend down | Check Vercel status, rollback if needed |
| Backend down | Check Render status, check database |
| Database down | Check Render PostgreSQL status |
| External API failing | Check Yahoo Finance / Alpha Vantage status |

---

## Useful Commands

```bash
# Check backend health
curl https://stock-tracker-api.onrender.com/health

# Check frontend
curl https://stock-tracker-frontend.vercel.app

# View backend logs (Render CLI)
render logs --service=stock-tracker-api

# Vercel deployment status
vercel ls
```

---

*Last Updated: 2026-04-04*
