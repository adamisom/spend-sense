# Railway Port Configuration Fix

## Issue
Railway sets `PORT=8080` internally, but public networking routes to port `8000`. This mismatch caused 502 errors.

## Solution
Hardcoded port `8000` in `scripts/railway_start.sh` to match Railway's public networking configuration.

## Files Changed
- `scripts/railway_start.sh` - Forces port 8000 regardless of `PORT` env var

