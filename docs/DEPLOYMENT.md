# SpendSense Deployment Guide - Railway

## Quick Deploy to Railway

### Prerequisites
- Railway account (sign up at https://railway.app)
- GitHub repository with SpendSense code
- Railway CLI (optional, for local testing)

### Step 1: Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your SpendSense repository
5. Railway will auto-detect the Dockerfile

### Step 2: Configure Environment Variables

In Railway dashboard, go to your service → Variables tab, add:

**Required:**
```
STREAMLIT_PASSWORD=your_secure_password_here
DATABASE_PATH=/app/db/spend_sense.db
```

**Note**: Plain text password is used for simplicity. For high-trust, low-user scenarios this is sufficient.

### Step 3: Deploy

Railway will automatically:
1. Build the Docker image using `Dockerfile.railway`
2. Deploy the service
3. Assign a public URL (e.g., `https://spendsense-production.up.railway.app`)

### Step 4: Initialize Database

After first deployment, you need to initialize the database:

1. Open Railway dashboard → Your service → Deployments
2. Click on the latest deployment → View Logs
3. Open the service shell/terminal
4. Run:
```bash
python -c "from src.db.connection import initialize_db; initialize_db()"
python -m src.ingest.data_generator --users 50
python scripts/load_data.py
python scripts/compute_signals.py
python scripts/generate_recommendations.py --all
```

### Step 5: Access Your Dashboard

1. Railway provides a public URL (e.g., `https://your-app.up.railway.app`)
2. Visit the URL
3. Enter the password you set in `STREAMLIT_PASSWORD`
4. Dashboard should load!

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `STREAMLIT_PASSWORD` | Yes | - | Plain text password for basic auth |
| `STREAMLIT_PASSWORD_HASH` | No | - | SHA256 hash of password (alternative to plain text) |
| `DATABASE_PATH` | No | `db/spend_sense.db` | Path to SQLite database file |
| `PORT` | Auto | - | Railway sets this automatically |
| `PYTHONPATH` | Auto | `/app` | Python path (set in Dockerfile) |

## Security Notes

- **Basic Auth**: Simple password protection for high-trust, low-user scenarios
- **HTTPS**: Railway automatically provides HTTPS
- **Database**: SQLite file is ephemeral (resets on redeploy) - use Railway volumes for persistence
- **Rate Limiting**: Basic rate limiting implemented in guardrails

## Persistent Database (Optional)

To persist database across deployments:

1. In Railway dashboard → Your service → Settings
2. Add a volume mount:
   - Mount path: `/app/db`
   - This will persist the database file

## Testing Authentication Locally

Before deploying, test authentication locally:

```bash
# Set password environment variable
export STREAMLIT_PASSWORD=test123

# Run Streamlit
streamlit run src/ui/streamlit_app.py

# Visit http://localhost:8501
# Should see password prompt
# Enter: test123
# Should see dashboard
```


## Troubleshooting

### Dashboard shows "Password incorrect"
- Check `STREAMLIT_PASSWORD` environment variable is set correctly
- Verify no extra spaces in password
- Test locally first with `export STREAMLIT_PASSWORD=test` before deploying

### Authentication not working
- Verify environment variable is set in Railway dashboard
- Check Railway logs for errors
- Ensure variable name is exactly `STREAMLIT_PASSWORD` (not `STREAMLIT_PASS` or similar)
- Try redeploying after setting environment variable

### Database not found
- Run initialization commands in Railway shell
- Check `DATABASE_PATH` environment variable

### Service won't start
- Check Railway logs for errors
- Verify Dockerfile.railway exists
- Check that all dependencies are in requirements.txt

### Port issues
- Railway sets `PORT` automatically - don't override it
- Streamlit will use `$PORT` environment variable

## Cost Monitoring

Railway provides:
- Free tier: $5 credit/month
- Usage-based pricing after free tier
- Monitor usage in Railway dashboard → Usage

**Cost-saving tips:**
- Use Railway volumes only if needed (persistent database)
- Monitor deployment logs for errors
- Set up Railway alerts for high usage

## Manual Testing After Deployment

See `docs/MANUAL_TESTING.md` for post-deployment testing checklist.

