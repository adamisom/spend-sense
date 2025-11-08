# Restart Streamlit to Fix 404 Errors

The directory structure has changed (pages → components), so Streamlit needs to be restarted.

## Steps:

1. **Stop the current Streamlit server:**
   - Press `Ctrl+C` in the terminal where Streamlit is running, OR
   - Find and kill the process: `pkill -f streamlit`

2. **Clear browser cache (important!):**
   - In Chrome: Press `Cmd+Shift+Delete` (Mac) or `Ctrl+Shift+Delete` (Windows)
   - Select "Cached images and files"
   - Click "Clear data"
   - OR use Incognito/Private mode

3. **Restart Streamlit:**
   ```bash
   streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
   ```

4. **Access the dashboard:**
   - Go to: `http://localhost:8501` (NOT `/recommendation_engine`)
   - Use the sidebar selectbox to navigate between pages
   - Do NOT try to access pages via URL routes like `/recommendation_engine`

## Why this happened:
- Streamlit was treating `pages/` as a multi-page app structure
- We renamed it to `components/` to fix this
- Streamlit needs a restart to pick up the new structure
- Browser cache might still have old route references

## If still having issues:
- Make sure you're accessing `http://localhost:8501` (root URL)
- Use the sidebar navigation, not direct URLs
- Check that `src/ui/components/` exists (not `pages/`)
