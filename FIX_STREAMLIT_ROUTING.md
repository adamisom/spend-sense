# Fix Streamlit Routing Issues

## The Problem
Streamlit is trying to use multi-page app routing when you access URLs like `/recommendation_engine` directly. This causes 404 errors because we're using a single-page app with sidebar routing.

## Solution

### 1. **Always access the root URL:**
   ```
   http://localhost:8501
   ```
   **NOT** `http://localhost:8501/recommendation_engine`

### 2. **Use the sidebar navigation:**
   - Use the "Select View" dropdown in the sidebar
   - Do NOT type URLs directly in the browser

### 3. **If you see the error:**
   - Go back to `http://localhost:8501` (root URL)
   - Clear browser cache: `Cmd+Shift+Delete` (Mac) or `Ctrl+Shift+Delete` (Windows)
   - Use the sidebar to navigate

### 4. **Restart Streamlit after directory changes:**
   ```bash
   # Stop current instance (Ctrl+C)
   # Then restart:
   streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
   ```

## Why This Happens
- Streamlit automatically detects a `pages/` directory and enables multi-page routing
- We renamed `pages/` → `components/` to disable this
- But if you access `/recommendation_engine` directly, Streamlit still tries multi-page routing
- Our app uses single-page routing via sidebar selectbox

## Current Setup
- ✅ Single-page app with sidebar routing
- ✅ All components in `src/ui/components/` (not `pages/`)
- ✅ Main app: `src/ui/streamlit_app.py`
- ✅ Navigation via sidebar selectbox only

