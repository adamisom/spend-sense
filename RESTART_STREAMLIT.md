# Starting and Stopping Streamlit Dashboard

## 🔍 Check if Streamlit is Running

**Check if running in Docker:**
```bash
docker ps | grep spendsense
# If you see 'spendsense-dev' or 'spendsense-app', it's running in Docker
```

**Check if running locally:**
```bash
lsof -i :8501
# If you see a process, Streamlit is running on port 8501
```

**Check for any Streamlit process:**
```bash
ps aux | grep streamlit | grep -v grep
```

## 🛑 Stop Streamlit

**If running in Docker:**
```bash
# Stop the container
docker stop spendsense-dev
# Or stop all containers
docker-compose down
```

**If running locally:**
```bash
# Press Ctrl+C in the terminal where Streamlit is running, OR
pkill -f streamlit
# Or kill process on port 8501
lsof -ti:8501 | xargs kill -9
```

## ▶️ Start Streamlit

**Option 1: Run locally (recommended for development)**
```bash
# From project root
streamlit run src/ui/streamlit_app.py
```
Access at: `http://localhost:8501`

**Option 2: Run in Docker container**
```bash
# Start container
docker-compose up -d

# Then exec into container and run Streamlit
docker-compose exec spendsense-app streamlit run src/ui/streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

**Option 3: Use Makefile**
```bash
make ui
```

## 🔄 When to Restart Streamlit

**Always restart after:**
- Making changes to `src/ui/streamlit_app.py` or any UI component files
- Changing database schema or connection logic
- Modifying environment variables or configuration
- Seeing 404 errors or stale data in the UI
- Code changes not reflecting in the browser

**How to restart:**
1. Stop Streamlit (see "Stop Streamlit" above)
2. Start Streamlit again (see "Start Streamlit" above)
3. **Clear browser cache** if issues persist:
   - Chrome: `Cmd+Shift+Delete` (Mac) or `Ctrl+Shift+Delete` (Windows)
   - Select "Cached images and files" → "Clear data"
   - OR use Incognito/Private mode

## 📍 Accessing the Dashboard

- **URL**: `http://localhost:8501` (root URL only)
- **Navigation**: Use the sidebar selectbox to navigate between pages
- **Do NOT** try to access pages via URL routes like `/recommendation_engine` (Streamlit doesn't support routing)

## 🐛 Troubleshooting

**Port 8501 already in use:**
```bash
# Find what's using the port
lsof -i :8501

# Kill it
lsof -ti:8501 | xargs kill -9
```

**Changes not reflecting:**
1. Restart Streamlit (see above)
2. Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
3. Clear browser cache (see above)

**404 errors:**
- Make sure you're accessing `http://localhost:8501` (root URL)
- Use the sidebar navigation, not direct URLs
- Check that `src/ui/components/` exists (not `pages/`)
