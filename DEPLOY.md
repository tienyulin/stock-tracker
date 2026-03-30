# Stock Tracker - Deployment Guide (Free Tier)

**Stack:**
- Frontend: Vercel (free, unlimited)
- Backend: Render.com (free tier, FastAPI)
- Database: Neon PostgreSQL (free tier)
- Redis: Upstash (free serverless Redis)

---

## 1. Database Setup - Neon

1. Go to https://neon.tech
2. Sign up (GitHub OAuth)
3. Create new project:
   - Name: `stock-tracker`
   - Region: choose closest to you
4. In Dashboard → Connection Details → Copy connection string:
   ```
   postgresql://user:password@ep-xxx-xxx-123456.us-east-2.aws.neon.tech/stocktracker?sslmode=require
   ```
5. Create `.env` in project root with:
   ```
   DATABASE_URL=postgresql://user:password@ep-xxx-xxx-123456.us-east-2.aws.neon.tech/stocktracker?sslmode=require
   ```

---

## 2. Redis Setup - Upstash

1. Go to https://upstash.com
2. Sign up (GitHub OAuth)
3. Create new Redis database:
   - Name: `stock-tracker`
   - Region: choose closest
4. In dashboard → REST API → Copy connection string:
   ```
   redis://default:xxxxx@xxx.upstash.io:6379
   ```
5. Add to `.env`:
   ```
   REDIS_URL=redis://default:xxxxx@xxx.upstash.io:6379
   ```

---

## 3. Backend Deployment - Render.com

### Option A: Deploy from GitHub (Recommended)

1. Go to https://render.com
2. "New" → "Web Service"
3. Connect GitHub → Select `stock-tracker` repo
4. Configure:
   | Setting | Value |
   |---------|-------|
   | Name | `stock-tracker-api` |
   | Region | Singapore (or closest) |
   | Branch | `develop` |
   | Runtime | `Python 3` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | Free instance | Yes |

5. Add Environment Variables:
   - `DATABASE_URL` → from Neon
   - `REDIS_URL` → from Upstash
   - `ALLOWED_HOSTS` → `.onrender.com`
   - `PORT` → `10000`

6. Click "Deploy"

### Option B: Create render.yaml (Infrastructure as Code)

Already compatible - Render auto-detects `render.yaml` or `render.txt`.

After first deploy, set custom domain or use the provided `.onrender.com` URL:
```
https://stock-tracker-api.onrender.com
```

---

## 4. Frontend Deployment - Vercel

### Option A: Deploy from GitHub (Recommended)

1. Go to https://vercel.com
2. "Add New Project" → Import `stock-tracker`
3. Configure:
   | Setting | Value |
   |---------|-------|
   | Framework | `Vite` (detected) |
   | Root Directory | `frontend` |
   | Build Command | `npm run build` |
   | Output Directory | `dist` |
   | Environment Variables | See below |

4. Add Environment Variable:
   - `VITE_API_BASE_URL` → `https://stock-tracker-api.onrender.com/api/v1`
   - `VITE_API_TARGET` → `https://stock-tracker-api.onrender.com`

5. Click "Deploy"

### Option B: Vercel CLI

```bash
cd frontend
vercel --prod
```

---

## 5. Verify Deployment

### Backend Health Check
```bash
curl https://stock-tracker-api.onrender.com/health
# Expected: {"status":"healthy"}
```

### API Docs
```
https://stock-tracker-api.onrender.com/docs
```

### Frontend
- Vercel will provide URL: `https://stock-tracker-xxx.vercel.app`
- Internal team only - no public promotion

---

## 6. Environment Update (After Backend URL is known)

Once backend is deployed, update frontend:

1. In Vercel dashboard → frontend project → Settings → Environment Variables
2. Set `VITE_API_BASE_URL` to actual backend URL (e.g., `https://stock-tracker-api.onrender.com/api/v1`)
3. Redeploy frontend

---

## Troubleshooting

### Backend not starting
- Check Render logs: Dashboard → service → Logs
- Verify `DATABASE_URL` and `REDIS_URL` are set
- Ensure `requirements.txt` is in root

### Frontend API calls failing
- Check browser console for CORS or network errors
- Verify `VITE_API_BASE_URL` is set correctly
- Ensure backend CORS is configured for Vercel domain

### Database connection issues
- Neon requires `?sslmode=require` in connection string
- Check connection string format

---

## Cost Summary

| Service | Tier | Monthly Cost |
|---------|------|-------------|
| Vercel | Hobby (Free) | $0 |
| Render | Free | $0 |
| Neon | Free | $0 |
| Upstash | Free | $0 |
| **Total** | | **$0** |

---

## Internal Team URLs (Example)

After deployment, share with team:
- **Frontend**: `https://stock-tracker-xxx.vercel.app`
- **Backend API**: `https://stock-tracker-api.onrender.com`
- **API Docs**: `https://stock-tracker-api.onrender.com/docs`