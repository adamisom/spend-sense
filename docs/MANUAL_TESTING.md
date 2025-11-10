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
- [ ] See page explanation expander ("ℹ️ What is this page?")
- [ ] See action buttons at top:
  - [ ] "🔄 Refresh Data" button (reloads all data from database)
  - [ ] "🔧 Compute Signals" button (computes signals for all users)
- [ ] See key metrics:
  - [ ] Total Users count
  - [ ] Signal Coverage percentage
  - [ ] Avg Data Quality score
  - [ ] 24h Recommendations count
- [ ] See system status cards (Recommendation Engine, Signal Detection)
- [ ] Click "🔄 Refresh Data" → Metrics update

### Test 3: User View Page (5 min)

- [ ] Navigate to "User View"
- [ ] See info box: "👁️ Operator View: This page shows a mock of the end-user web application experience"
- [ ] Enter user ID (e.g., `user_001`) or click a user ID from the list
- [ ] Click "🔍 Load My Profile"
- [ ] See consent management section:
  - [ ] Current consent status displayed
  - [ ] "Grant Consent" or "Revoke Consent" button works
- [ ] See persona card with:
  - [ ] Persona name and icon
  - [ ] Persona description
  - [ ] Matched criteria
- [ ] See "🔄 Get New Recommendations" button
- [ ] See recommendations section:
  - [ ] 3-5 recommendations displayed
  - [ ] Each recommendation has:
    - [ ] Title
    - [ ] Description
    - [ ] "Why this matters" rationale (personalized)
    - [ ] Disclaimer: "This is educational content, not financial advice. Consult a licensed advisor for personalized guidance."
    - [ ] Reading time
    - [ ] Content type
- [ ] Test consent blocking: Revoke consent for a user → Recommendations should be blocked with warning message

### Test 4: User Analytics Page (2 min)

- [ ] Navigate to "User Analytics"
- [ ] See user overview metrics
- [ ] See persona distribution:
  - [ ] Pie chart showing personas
  - [ ] Table with persona counts
- [ ] See data quality histogram
- [ ] See user list table (filterable)

### Test 5: Recommendation Engine Page (3 min)

- [ ] Navigate to "Recommendation Engine"
- [ ] Wait for page to load (may take a few seconds)
- [ ] See page explanation expander ("ℹ️ What is this page?")
- [ ] See filter controls:
  - [ ] Filter by Status dropdown (All, Pending, Approved, Rejected)
  - [ ] Limit number input
  - [ ] "🔄 Refresh" button (styled, full-width)
- [ ] See approval queue or recent recommendations
- [ ] Each recommendation shows:
  - [ ] User ID
  - [ ] Content title
  - [ ] Rationale
  - [ ] Status badge (Pending, Approved, Rejected)
  - [ ] Created timestamp
  - [ ] "🔍 View Decision Trace (Audit Trail)" expander
- [ ] Click decision trace expander:
  - [ ] Full JSON trace displays
  - [ ] Step-by-step summary shows (persona classification, signal mapping, filtering, scoring)
- [ ] Test "🔄 Refresh" button → Page reloads with latest recommendations
- [ ] Test status filtering → Only shows recommendations matching filter
- [ ] Test approve/reject buttons (if pending recommendations exist)

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

### Test 10: Signal Computation (5 min)

- [ ] Navigate to "System Overview" page
- [ ] Click "🔧 Compute Signals" button (on System Overview page, not sidebar)
- [ ] See info message: "🔄 Computing signals for all users... This may take 1-2 minutes. Please wait."
- [ ] See spinner: "⏳ Processing... This may take a few minutes."
- [ ] Wait for completion (may take 1-2 minutes)
- [ ] See success message: "✅ Signal computation complete for X users!"
- [ ] Page auto-refreshes after 3 seconds
- [ ] Signal coverage increases
- [ ] User Analytics page shows updated signals
- [ ] User personas appear (colored icons in User View instead of gray)

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

### Test 12: Refresh Data Button (2 min)

- [ ] Navigate to "System Overview" page
- [ ] Click "🔄 Refresh Data" button
- [ ] Verify metrics update (check last refresh timestamp in sidebar)
- [ ] All pages should show latest data after refresh

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
