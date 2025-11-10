# Railway Quick Deploy Guide

## 🚀 Deploy (5 minutes)

### 1. Create Project
- Go to https://railway.app
- Click **"New Project"**
- Select **"Deploy from GitHub repo"**
- Choose `spend-sense` repository
- Railway auto-detects Dockerfile

### 2. Set Environment Variables
In Railway dashboard → Your service → **Variables** tab:

```
STREAMLIT_PASSWORD=your_password_here
DATABASE_PATH=/app/db/spend_sense.db
```

### 3. Deploy
- Railway automatically builds and deploys
- Wait for deployment to complete (~2-3 minutes)
- Copy the public URL (e.g., `https://spendsense-production.up.railway.app`)

### 4. Initialize Database
Railway dashboard → Your service → Click **"Shell"** or **"Terminal"** button (top right of service view):

```bash
python -c "from src.db.connection import initialize_db; initialize_db()"
python -m src.ingest.data_generator --users 50
python scripts/load_data.py
python scripts/compute_signals.py
python scripts/generate_recommendations.py --all
```

**Note**: The Shell opens a terminal session in your running container. If you don't see a Shell button, use Railway CLI: `railway shell`

---

## ✅ Smoke Test (2 minutes)

### Test 1: Authentication
- [ ] Visit Railway URL
- [ ] See password prompt
- [ ] Enter password → Dashboard loads

### Test 2: System Overview
- [ ] Navigate to "System Overview"
- [ ] See metrics: Users > 0, Signal Coverage > 0%
- [ ] No errors

### Test 3: User View
- [ ] Navigate to "User View"
- [ ] Enter `user_001`
- [ ] Click "🔍 Load My Profile"
- [ ] See persona card + recommendations

### Test 4: Navigation
- [ ] Click through all pages (no crashes):
  - User Analytics
  - Recommendation Engine
  - Data Quality
  - Performance Metrics

**✅ All pass = Deployment successful!**

---

## 🐛 Quick Fixes

**Password not working?**
- Check `STREAMLIT_PASSWORD` is set in Railway variables
- Redeploy after setting variable

**Database errors?**
- Run initialization commands in Railway shell (step 4 above)

**Service won't start?**
- Check Railway logs for errors
- Verify `Dockerfile.railway` exists

