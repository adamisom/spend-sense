# Railway Port Configuration Fix

## Issue
The app was getting 502 errors ("Application failed to respond") after deployment. Logs showed:
- Railway sets `PORT=8080` environment variable
- App was starting on port 8080
- But Railway couldn't reach the app

## What We Tried
1. Initially tried using `${PORT:-8000}` to default to 8000 if PORT not set
2. Added debug logging which confirmed Railway sets `PORT=8080`
3. Hardcoded port `8000` in startup script as a workaround

## Solution
Hardcoded port `8000` in `scripts/railway_start.sh` to force the app to listen on 8000, regardless of Railway's `PORT` env var.

## Uncertainty
**Note**: The root cause is unclear. Public networking configuration in Railway may not automatically route to a specific port. The fix (hardcoding 8000) works but the exact reason for the original 502 errors is not fully understood. Railway's port routing behavior may differ from expectations.

## Files Changed
- `scripts/railway_start.sh` - Forces port 8000 regardless of `PORT` env var

