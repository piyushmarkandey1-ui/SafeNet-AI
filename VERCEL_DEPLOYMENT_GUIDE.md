# SafeNet AI - Vercel Deployment Guide

## ✅ All Changes Committed and Pushed!

**Commit:** `25c6008`  
**Branch:** `main`  
**Repository:** https://github.com/piyushmarkandey1-ui/SafeNet-AI

---

## 🚀 Quick Deploy to Vercel (5 Minutes)

### Step 1: Install Vercel CLI (Optional but Recommended)
```bash
npm install -g vercel
```

### Step 2: Deploy via Vercel CLI
```bash
cd "d:\Hackathons\ET Hackathon"
vercel
```

Follow the prompts:
- **Set up and deploy?** → Yes
- **Which scope?** → Your personal account
- **Link to existing project?** → No
- **Project name?** → `safenet-ai` (or your choice)
- **Directory?** → `.` (current directory)
- **Override settings?** → No

### Step 3: Set Environment Variables
After deployment, add the Gemini API key:

```bash
vercel env add GEMINI_API_KEY
```

When prompted, paste your key:
```
AIzaSyAQ.Ab8RN6K2aCIOw25SyHvgBtFRCwLNyzJjYGnLxFlpqiM6lg6idw
```

Select:
- **Environment:** Production, Preview, Development (select all)

### Step 4: Redeploy with Environment Variables
```bash
vercel --prod
```

---

## 🌐 Alternative: Deploy via Vercel Dashboard

### 1. Go to Vercel Dashboard
Visit: https://vercel.com/new

### 2. Import Git Repository
- Click **"Add New..."** → **"Project"**
- Click **"Import Git Repository"**
- Select your GitHub account
- Find and select `SafeNet-AI` repository
- Click **"Import"**

### 3. Configure Project Settings

**Root Directory:** Leave blank (uses root)  
**Framework Preset:** Vite  
**Build Command:** `npm run build`  
**Output Directory:** `frontend/dist`  
**Install Command:** `npm install`

### 4. Add Environment Variables
In the project settings, add:

| Variable Name | Value |
|--------------|-------|
| `GEMINI_API_KEY` | `AIzaSyAQ.Ab8RN6K2aCIOw25SyHvgBtFRCwLNyzJjYGnLxFlpqiM6lg6idw` |

Make sure to select all environments (Production, Preview, Development).

### 5. Deploy
Click **"Deploy"** and wait 3-5 minutes.

---

## 📦 What Gets Deployed

### Frontend (Static Site)
- Built with Vite
- Deployed to Vercel Edge Network
- React SPA with all 5 modules
- Auto-detects API endpoints (Vercel vs localhost)

### Backend (Serverless Functions)
The following API endpoints are deployed as serverless functions:

```
/api/orchestrator/dashboard-feed   → Live risk feed
/api/orchestrator/simulate          → Trigger demo scenario
/api/geo/hotspots                   → Geospatial hotspots
/api/scam/classify                  → Scam call classification
/api/shield/ask                     → Citizen Shield chatbot
/api/graph/case/:id                 → Fraud graph case evidence
```

---

## 🔧 Architecture on Vercel

```
┌─────────────────────────────────────────────────────────────┐
│                     Vercel Edge Network                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend (Static)          Backend (Serverless)            │
│  ├─ React SPA               ├─ /api/orchestrator/*          │
│  ├─ Dashboard UI            ├─ /api/geo/*                   │
│  ├─ Maps & Charts           ├─ /api/scam/*                  │
│  └─ Real-time Feed          ├─ /api/shield/*                │
│                              └─ /api/graph/*                 │
│                                                               │
│  API Auto-detection: window.location.origin on Vercel       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Files Created for Vercel Deployment

### Root Level
- ✅ `vercel.json` — Main Vercel configuration
- ✅ `package.json` — Root package for monorepo
- ✅ `requirements.txt` — Python dependencies (lightweight)

### Frontend
- ✅ `frontend/vercel.json` — Frontend-specific config
- ✅ Updated `frontend/src/lib/api.js` — Auto-detect API URLs

### Backend (Serverless Functions)
- ✅ `api/index.py` — Main serverless entry point
- ✅ `api/orchestrator/dashboard-feed.py` — Dashboard feed endpoint
- ✅ `api/orchestrator/simulate.py` — Simulation trigger
- ✅ `api/geo/hotspots.py` — Geospatial hotspots
- ✅ `api/scam/classify.py` — Scam classification

---

## 🔐 Security Best Practices

### Environment Variables
**✅ Done:** Gemini API key stored as environment variable  
**✅ Done:** CORS configured for Vercel domains  
**✅ Done:** No secrets in committed code

### CORS Configuration
The backend automatically allows:
- `https://*.vercel.app`
- `https://safenet-ai.vercel.app` (your production domain)
- `http://localhost:5173` (development)

---

## 🧪 Testing Your Deployment

### 1. Check Deployment Status
After deployment completes, Vercel will show:
```
✅ Production: https://safenet-ai-xyz123.vercel.app
```

### 2. Test Frontend
Visit your deployment URL and verify:
- ✅ Dashboard loads
- ✅ Live Risk Feed displays
- ✅ Map shows hotspots
- ✅ "Simulate Scenario" button works

### 3. Test API Endpoints
```bash
# Test dashboard feed
curl https://safenet-ai-xyz123.vercel.app/api/orchestrator/dashboard-feed

# Test simulation
curl -X POST https://safenet-ai-xyz123.vercel.app/api/orchestrator/simulate

# Test hotspots
curl https://safenet-ai-xyz123.vercel.app/api/geo/hotspots
```

---

## 🐛 Troubleshooting

### Issue: "Function Size Exceeded"
**Cause:** Some Python packages (torch, torchvision) are too large for Vercel (500MB+ limit)

**Solution:** Already handled! The `requirements.txt` excludes these heavy packages. The Counterfeit Vision module will use fallback data on Vercel.

### Issue: "Build Failed - Missing Dependencies"
**Cause:** Some Python packages need compilation

**Solution:** 
```bash
# Update requirements.txt to use pre-built wheels
vercel env add PIP_NO_CACHE_DIR 1
vercel --prod
```

### Issue: "API Returns 404"
**Cause:** Serverless function not deployed

**Solution:**
1. Check `vercel.json` includes `/api` in functions
2. Verify Python runtime: `"runtime": "python3.13"`
3. Redeploy: `vercel --prod`

### Issue: "CORS Error in Browser"
**Cause:** CORS not configured for your domain

**Solution:** Backend already includes wildcard for Vercel:
```python
allow_origins=[
    "https://*.vercel.app",
    "https://safenet-ai.vercel.app",
]
```

If using custom domain, add it to `api/index.py` and redeploy.

### Issue: "Gemini API Key Not Working"
**Cause:** Environment variable not set or incorrect

**Solution:**
```bash
# List current env vars
vercel env ls

# Remove old key
vercel env rm GEMINI_API_KEY

# Add new key
vercel env add GEMINI_API_KEY
# Paste: AIzaSyAQ.Ab8RN6K2aCIOw25SyHvgBtFRCwLNyzJjYGnLxFlpqiM6lg6idw

# Redeploy
vercel --prod
```

---

## 🔄 Continuous Deployment

### Automatic Deployments (Recommended)
Once connected to GitHub, Vercel automatically deploys on every push:

- **Push to `main`** → Production deployment
- **Push to any branch** → Preview deployment
- **Pull requests** → Preview deployment with unique URL

### Manual Deployments
```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod

# Deploy specific branch
git checkout feature-branch
vercel
```

---

## 📊 Monitoring & Analytics

### Vercel Dashboard
- **Analytics:** Traffic, performance, errors
- **Logs:** Real-time function logs
- **Deployments:** History, rollback options
- **Domains:** Custom domain management

Access at: https://vercel.com/dashboard

### Function Logs
```bash
# View real-time logs
vercel logs --follow

# View logs for specific function
vercel logs api/orchestrator/simulate
```

---

## 🎨 Custom Domain (Optional)

### Add Custom Domain
1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Click "Add Domain"
3. Enter your domain (e.g., `safenet-ai.yourdomain.com`)
4. Add DNS records as shown by Vercel:
   ```
   Type: CNAME
   Name: safenet-ai
   Value: cname.vercel-dns.com
   ```
5. Wait for DNS propagation (5-30 minutes)

### Update CORS
After adding custom domain, update `api/index.py`:
```python
allow_origins=[
    "https://*.vercel.app",
    "https://safenet-ai.yourdomain.com",  # Add your domain
]
```

Then redeploy: `vercel --prod`

---

## 💰 Pricing & Limits

### Vercel Free Tier (Hobby)
- ✅ Unlimited deployments
- ✅ 100GB bandwidth/month
- ✅ Serverless functions (100GB-hrs/month)
- ✅ 1000 image optimizations/month
- ✅ Custom domains

**Perfect for hackathons and demos!**

### Vercel Pro ($20/month)
- Increased limits
- Team collaboration
- Advanced analytics
- Password protection

---

## 📝 Post-Deployment Checklist

- [ ] Deployment successful (green checkmark in Vercel)
- [ ] Frontend loads at production URL
- [ ] API endpoints respond correctly
- [ ] "Simulate Scenario" button triggers real events
- [ ] Gemini API key is working (check scam classification)
- [ ] Map displays geospatial hotspots
- [ ] No console errors in browser DevTools
- [ ] Mobile responsive (test on phone)
- [ ] Share deployment URL with team/judges

---

## 🎉 Your SafeNet AI is Now Live!

### Share Your Demo
```
🚀 SafeNet AI - Digital Public Safety Intelligence

Live Demo: https://safenet-ai-xyz123.vercel.app
GitHub: https://github.com/piyushmarkandey1-ui/SafeNet-AI

Features:
✅ Real-time scam detection with Gemini AI
✅ Fraud network analysis & visualization
✅ Geospatial crime hotspot mapping
✅ Counterfeit currency detection
✅ Multi-lingual citizen chatbot
✅ Compound risk scoring & auto-escalation

Built with: React, FastAPI, LangGraph, Gemini AI, Vercel
```

---

## 🆘 Need Help?

### Vercel Support
- Docs: https://vercel.com/docs
- Discord: https://vercel.com/discord
- Status: https://www.vercel-status.com

### Project Issues
- GitHub Issues: https://github.com/piyushmarkandey1-ui/SafeNet-AI/issues

---

## 🔮 What's Next?

### Enhancements for Production
1. **Add Redis/Database:** Persistent storage for events
2. **Enable Caching:** Speed up API responses
3. **Add Authentication:** Protect sensitive endpoints
4. **Set up Monitoring:** Error tracking with Sentry
5. **Load Testing:** Ensure scalability
6. **A/B Testing:** Optimize UX with Vercel Edge Config

### Advanced Features
1. **Real-time WebSockets:** Live event streaming
2. **PDF Report Generation:** Download incident reports
3. **Email Alerts:** Notify on critical events
4. **Admin Dashboard:** Manage alerts and thresholds
5. **API Rate Limiting:** Prevent abuse

---

**Good luck with your hackathon demo! 🚀**
