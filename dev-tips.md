# 🚀 SpendSense Developer Speed Tips

## ⚡ Fastest Development Workflow

### 🔥 Daily 5-Second Startup
```bash
# Start Docker daemon (once per session)
colima start

# Terminal 1 (main development)  
make up && make shell

# Terminal 2 (tests, in parallel)
make test
```

### 🧪 Lightning Fast Testing Loop
```bash
# Instead of: docker-compose exec spendsense-app python -m pytest tests/test_features.py
# Use: 
make quick-test FILE=test_features.py

# Even faster for single functions:
make shell
pytest tests/test_features.py::test_subscription_detection -v
```

### 🔄 Ultra-Quick Code Changes
1. **Edit code in your IDE** (changes are instantly synced)
2. **Run in container**: `python -m src.ingest.data_generator --users 5`
3. **See results immediately** (no rebuild, no restart)

## 🎯 IDE Setup for Maximum Speed

### VS Code (Recommended)
1. Install Python extension
2. Use the provided `.vscode/settings.json` (already configured)  
3. **For container development**: Install "Remote - Containers" extension

### IDE Hot Tips
- **Linting works**: Code is analyzed in real-time
- **Debugging works**: Set breakpoints normally 
- **IntelliSense works**: Auto-completion with container dependencies
- **Terminal integration**: Use `make shell` in IDE terminal

## 🚨 Common Speed Killers (Avoid These!)

### ❌ Slow Anti-Patterns
```bash
# DON'T: Rebuild container for every change
docker-compose build && docker-compose up

# DO: Use persistent container
make up  # (once per session)
```

```bash
# DON'T: Run full test suite constantly  
make test  # (only when needed)

# DO: Test specific files
make quick-test FILE=test_specific.py
```

```bash
# DON'T: Generate 50 users for quick tests
python -m src.ingest.data_generator --users 50

# DO: Use minimal data for speed
python -m src.ingest.data_generator --users 5
```

### ❌ Performance Traps
- **Never restart container** for code changes (volumes handle it)
- **Don't edit files inside container** (edit on host, sync is automatic)  
- **Avoid `docker-compose down`** unless necessary (loses running state)

## 🎪 Pro Development Tricks

### Multi-Terminal Setup
```bash
# Terminal 1: Main development
make shell

# Terminal 2: API server (background)
make shell
uvicorn src.api.routes:app --host 0.0.0.0 --reload &

# Terminal 3: Watch logs
make logs

# Terminal 4: Quick tests
make quick-test FILE=test_features.py
```

### Database Shortcuts
```bash
# Quick DB reset (10 seconds)
make reset-db

# Check DB without tools
make shell
sqlite3 /app/db/spend_sense.db "SELECT COUNT(*) FROM users;"
```

### Debug Mode
```bash
# Add debug prints anywhere in code
print(f"🐛 Debug: {variable_name}")

# See output immediately  
make logs
```

## 🏎️ Performance Expectations

With these optimizations:

| Task | Time | Method |
|------|------|--------|
| **First startup** | 30s | `make init` |
| **Daily startup** | 3s | `make up` |
| **Code change test** | 1s | Edit + run |
| **Full test suite** | 10s | `make test` |
| **Quick validation** | 1s | `make quick-run` |
| **DB reset** | 10s | `make reset-db` |

## 🎯 Development Mode vs Production

```bash
# Development (what you're using)
make up  # Fast, hot-reload, persistent data

# Production (future)
docker-compose -f docker-compose.prod.yml up  # Optimized for deployment
```

## 🆘 Troubleshooting Speed Issues

### ❌ "Cannot connect to the Docker daemon"
```bash
# SOLUTION: Start Colima first (most common issue!)
colima start

# Then try your command again
make init
```

### Container Feels Slow?
```bash
# Check container resources
docker stats spendsense-dev

# Rebuild if needed
make clean && colima restart && make init
```

### File Changes Not Syncing?
```bash
# Verify volume mounts
docker compose exec spendsense-app ls -la /app/src/

# Check volume performance  
make shell
echo "test" > /app/test.txt
exit
cat test.txt  # Should see "test"
```

### Database Issues?
```bash
# Quick reset
make reset-db

# Check health
make status
```

### Docker Commands Failing?
```bash
# Check if Colima is running
colima status

# If stopped, start it
colima start

# If broken, restart
colima restart
```

---

**🎯 Bottom Line**: With these optimizations, you should have **sub-second iteration cycles** for most development tasks. The container startup happens once, then everything is lightning fast!

