# Quick Verification Checklist

## What's Been Completed ✅

### Backend
- [x] Orchestrator router imported in `main.py`
- [x] Orchestrator router registered with FastAPI app
- [x] Three endpoints exposed:
  - `POST /orchestrator/event` — Ingest events for CRS computation
  - `GET /orchestrator/dashboard-feed` — Real source of truth for Live Risk Feed
  - `POST /orchestrator/simulate` — Triggers demo scenario

### Frontend
- [x] `getDashboardFeed()` updated to call `/orchestrator/dashboard-feed`
- [x] `simulateScenario()` function added to `api.js`
- [x] Dashboard `handleSimulate()` wired to call real backend
- [x] Polling mechanism implemented for live streaming effect (1.5s intervals × 8 = 12s total)
- [x] Graceful fallback to mocks when backend is unavailable

---

## Testing Right Now (Without Full Backend Running)

### 1. Frontend Mock Fallback Test
```bash
cd frontend
npm run dev
```

**Test:**
1. Open http://localhost:5173
2. Click "Simulate Scenario" button
3. **Expected:** Button triggers, console shows "Orchestrator not running or reachable"
4. **Expected:** Dashboard still shows mock data (no crashes)

**Status:** ✅ Frontend is resilient and functional even without backend

---

### 2. Code Structure Verification
You can verify the code changes were made correctly:

**Check backend integration:**
```bash
cd backend
# This will show the orchestrator router is imported and registered
grep -A 5 "orchestrator_router" app/main.py
```

**Check frontend integration:**
```bash
cd frontend
# This will show the new simulateScenario function
grep -A 10 "simulateScenario" src/lib/api.js

# This will show the updated handleSimulate
grep -A 15 "handleSimulate" src/components/dashboard/Dashboard.jsx
```

---

## Testing After Backend Dependencies Installed

### Step 1: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

**Required packages:** fastapi, uvicorn, pydantic, langgraph, networkx, scikit-learn, scipy, chromadb, etc.

**Note:** Installation was in progress but timed out due to slow network. Retry when network is stable.

---

### Step 2: Test Orchestrator Import
```bash
cd backend
python test_orchestrator_simple.py
```

**Expected output:**
```
✓ Import path configured
✓ Orchestrator API router imported successfully
✓ Router prefix: /orchestrator
✓ Available routes: 3
  - {'POST'} /event
  - {'GET'} /dashboard-feed
  - {'POST'} /simulate

✓ Orchestrator module is properly wired and ready to use!
```

---

### Step 3: Run Demo Scenario Standalone
```bash
cd backend
python -m app.orchestrator.demo_scenario
```

**Expected:** Full console output showing:
- Step 1: CRS ~35 (scam call only)
- Step 2: CRS ~65 (scam + fraud graph)
- Step 3: CRS ~87 (all signals converged → escalation)
- Incident report generated
- Audit log written

**Duration:** ~3-5 seconds with 1s delays between steps

---

### Step 4: Start Full Stack
```bash
# Terminal 1 (Backend)
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 (Frontend)  
cd frontend
npm run dev
```

**Expected backend output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Expected frontend output:**
```
  VITE v5.x.x  ready in 234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

---

### Step 5: End-to-End Dashboard Test

1. Open http://localhost:5173
2. Dashboard loads with initial data
3. Click **"Simulate Scenario"** button in top-right

**Expected behavior:**
- ✅ Button text changes to "Simulating..." with spinner icon
- ✅ Console shows: `Simulation started: { status: "simulation_started", message: "..." }`
- ✅ Live Risk Feed on left side starts updating
- ✅ Three events appear over ~6-10 seconds (one at a time)
- ✅ Events show increasing severity: MEDIUM → HIGH → CRITICAL
- ✅ Each event shows different Compound Risk Score
- ✅ Final event has red "CRITICAL" badge
- ✅ Click on final event → Evidence Panel opens on right with incident report
- ✅ Map shows hotspot visualization

**Timeline:**
```
t=0s     User clicks "Simulate Scenario"
t=0.1s   POST /orchestrator/simulate returns immediately
t=0.1s   Frontend starts polling every 1.5s
t=1.5s   First poll: Event 1 appears (scam call, CRS ~35)
t=3.0s   Second poll: Event 2 appears (fraud graph link, CRS ~65)
t=4.5s   Third poll: Event 3 appears (geo hotspot, CRS ~87, CRITICAL)
t=6-12s  Continued polling (shows any additional events)
t=12s    Polling stops automatically
```

---

## Debugging Tips

### If Backend Won't Start:
```bash
# Check if port 8000 is already in use
netstat -ano | findstr :8000

# Try a different port
uvicorn app.main:app --reload --port 8001
# Then update frontend api.js URLs to http://localhost:8001
```

### If Simulate Button Does Nothing:
1. Open browser DevTools (F12)
2. Go to Console tab
3. Click "Simulate Scenario"
4. Look for errors or `console.log('Simulation started: ...')`
5. Check Network tab for failed requests

### If Events Don't Appear:
1. Check browser console for API errors
2. Verify backend is running: http://localhost:8000/docs (FastAPI Swagger UI)
3. Test endpoint manually: `curl -X POST http://localhost:8000/orchestrator/simulate`
4. Check backend terminal for errors

### If ChromaDB/Embedding Errors:
The orchestrator graph tries to enrich events using Module C (fraud graph) and Module E (citizen shield), which use ChromaDB for RAG. If you see embedding-related errors:

**Option 1 - Skip enrichment (fastest for demo):**
Comment out the enrichment steps in `graph.py` (just for quick testing)

**Option 2 - Build indices (proper solution):**
```bash
cd backend
python -m app.fraud_graph.rag_query  # Builds fraud graph index
python -m app.citizen_shield.knowledge_base  # Builds shield KB
```

---

## Current Status

✅ **Code Integration:** 100% complete  
🔄 **Dependency Installation:** In progress (network timeout)  
⏳ **End-to-End Testing:** Pending backend dependencies  
✅ **Mock Fallback:** Verified working  

**Next Step:** Complete `pip install -r requirements.txt` when network is stable, then run Step 2-5 above.

---

## Files Ready for Review

1. `backend/app/main.py` — Orchestrator router wired
2. `frontend/src/lib/api.js` — Real endpoints + simulation trigger
3. `frontend/src/components/dashboard/Dashboard.jsx` — Real simulation handler with polling
4. `ORCHESTRATOR_INTEGRATION_COMPLETE.md` — Full implementation documentation
5. `backend/test_orchestrator_simple.py` — Quick import verification script

All changes follow the established architecture contract from Prompt 0. No UI components were modified (zero breaking changes). The mock→real swap is complete.
