# Manual Testing Guide - Post-Deployment

Quick testing checklist to verify nothing regressed and all basic functionality works.

## Pre-Testing Setup

1. **Access Dashboard**: Navigate to your Railway deployment URL
2. **Login**: Enter password set in `STREAMLIT_PASSWORD`
3. **Verify Access**: Should see dashboard without errors

---

## ✅ Basic Functionality Tests

### Test 1: Authentication (2 min)
- [ ] Visit dashboard URL
- [ ] See password prompt
- [ ] Enter correct password → Dashboard loads
- [ ] Enter wrong password → Error message shown
- [ ] Refresh page → Still logged in (session persists)

### Test 2: System Overview Page (2 min)
- [ ] Navigate to "System Overview"
- [ ] See key metrics:
  - [ ] Total Users count
  - [ ] Signal Coverage percentage
  - [ ] Avg Data Quality score
  - [ ] 24h Recommendations count
- [ ] See system status cards (Recommendation Engine, Signal Detection)
- [ ] Click "🔄 Refresh Data" → Metrics update

### Test 3: User View Page (3 min)
- [ ] Navigate to "User View"
- [ ] Enter user ID (e.g., `user_001`)
- [ ] Click "🔍 Load My Profile"
- [ ] See persona card with:
  - [ ] Persona name and icon
  - [ ] Persona description
  - [ ] Matched criteria
- [ ] See recommendations section:
  - [ ] 3-5 recommendations displayed
  - [ ] Each recommendation has:
    - [ ] Title
    - [ ] Description
    - [ ] "Why this matters" rationale
    - [ ] Reading time
    - [ ] Content type

### Test 4: User Analytics Page (2 min)
- [ ] Navigate to "User Analytics"
- [ ] See user overview metrics
- [ ] See persona distribution:
  - [ ] Pie chart showing personas
  - [ ] Table with persona counts
- [ ] See data quality histogram
- [ ] See user list table (filterable)

### Test 5: Recommendation Engine Page (2 min)
- [ ] Navigate to "Recommendation Engine"
- [ ] See approval queue or recent recommendations
- [ ] Each recommendation shows:
  - [ ] User ID
  - [ ] Content title
  - [ ] Rationale
  - [ ] Created timestamp

### Test 6: Data Quality Page (2 min)
- [ ] Navigate to "Data Quality"
- [ ] See quality distribution chart
- [ ] See quality metrics (average, median)
- [ ] See user list filtered by quality

### Test 7: Performance Metrics Page (2 min)
- [ ] Navigate to "Performance Metrics"
- [ ] See performance metrics:
  - [ ] P95 Compute Time
  - [ ] Error Rate
  - [ ] Avg Response Time
- [ ] See relevance metrics
- [ ] See fairness metrics (may show framework message if no demographics)

### Test 8: System Logs Page (1 min)
- [ ] Navigate to "System Logs"
- [ ] See recent log entries
- [ ] Logs are readable and formatted

---

## ✅ Regression Tests

### Test 9: Database Operations (3 min)
- [ ] All pages load without database errors
- [ ] No "database locked" errors
- [ ] Data persists across page refreshes
- [ ] Database path setting works (if changed in sidebar)

### Test 10: Signal Computation (5 min)
- [ ] Click "🔧 Compute Signals" in sidebar
- [ ] See spinner/loading indicator
- [ ] Wait for completion (may take 1-2 minutes)
- [ ] See success message
- [ ] Refresh page → Signal coverage increases
- [ ] User Analytics page shows updated signals

### Test 11: Navigation (2 min)
- [ ] Navigate between all pages:
  - [ ] User View
  - [ ] System Overview
  - [ ] User Analytics
  - [ ] Recommendation Engine
  - [ ] Data Quality
  - [ ] Performance Metrics
  - [ ] System Logs
- [ ] No page crashes or errors
- [ ] Sidebar navigation works correctly

### Test 12: Auto-Refresh (2 min)
- [ ] Enable "Auto-refresh (30s)" checkbox
- [ ] Wait 30+ seconds
- [ ] Verify data refreshes (check timestamp in sidebar)
- [ ] Disable auto-refresh
- [ ] Verify it stops refreshing

---

## ✅ API Endpoints (Optional - if API is exposed)

### Test 13: Health Check
```bash
curl https://your-app.up.railway.app/health
```
- [ ] Returns `{"status": "healthy"}`

### Test 14: User Profile
```bash
curl https://your-app.up.railway.app/profile/user_001
```
- [ ] Returns user profile with persona and signals

### Test 15: Recommendations
```bash
curl https://your-app.up.railway.app/recommendations/user_001
```
- [ ] Returns recommendations for user

---

## ✅ Edge Cases

### Test 16: Invalid User ID (1 min)
- [ ] In User View, enter invalid user ID (e.g., `invalid_user`)
- [ ] See appropriate error message
- [ ] No crash or stack trace

### Test 17: Empty Database (2 min)
- [ ] If database is empty, pages should show helpful messages
- [ ] No crashes or errors
- [ ] Clear instructions on how to populate data

### Test 18: Missing Data (2 min)
- [ ] Test with user that has no signals
- [ ] Test with user that has no recommendations
- [ ] Appropriate fallback messages shown

---

## ✅ Performance Checks

### Test 19: Page Load Times (2 min)
- [ ] System Overview loads in < 3 seconds
- [ ] User View loads in < 3 seconds
- [ ] User Analytics loads in < 5 seconds
- [ ] No excessive loading spinners

### Test 20: Responsiveness (2 min)
- [ ] Dashboard is responsive (works on mobile/tablet)
- [ ] Charts render correctly
- [ ] Tables are scrollable if needed

---

## ✅ Security Checks

### Test 21: Authentication (2 min)
- [ ] Password required to access dashboard
- [ ] Wrong password shows error
- [ ] No password bypass possible
- [ ] Session persists correctly

### Test 22: Input Validation (2 min)
- [ ] SQL injection attempts fail gracefully
- [ ] XSS attempts are sanitized
- [ ] Invalid inputs show appropriate errors

---

## Quick Smoke Test (5 minutes)

If you're short on time, run these critical tests:

1. ✅ **Authentication**: Login works
2. ✅ **System Overview**: Page loads, shows metrics
3. ✅ **User View**: Can load user profile, see recommendations
4. ✅ **Navigation**: Can navigate between all pages
5. ✅ **No Crashes**: All pages load without errors

---

## Expected Results

After all tests:
- ✅ All pages load without errors
- ✅ All core functionality works
- ✅ No regressions from previous version
- ✅ Performance is acceptable (< 5s page loads)
- ✅ Authentication works correctly
- ✅ Database operations succeed

---

## Reporting Issues

If any test fails:
1. Note which test failed
2. Check Railway logs for errors
3. Verify environment variables are set correctly
4. Check database is initialized
5. Review error messages in dashboard

---

**Total Testing Time**: ~30-40 minutes for full test suite  
**Quick Smoke Test**: ~5 minutes

