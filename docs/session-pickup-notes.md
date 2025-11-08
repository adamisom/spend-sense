# Session Pickup Notes

Quick reference guide for continuing work on SpendSense.

## Generating Recommendations for Users

### Overview
The recommendation engine generates personalized content recommendations based on user signals and persona classification. Recommendations are saved to the `recommendations` table in the database.

### Prerequisites
Before generating recommendations, ensure:
1. **User signals are computed**: Users must have signals in the `user_signals` table
   ```bash
   python scripts/compute_signals.py --db-path db/spend_sense.db
   ```

2. **Database is initialized**: The database should have the `recommendations` table
   - Schema is in `db/schema.sql`
   - Table includes: `rec_id`, `user_id`, `content_id`, `rationale`, `created_at`, `approved`, `delivered`, `viewed_at`

### Generating Recommendations

#### For a Single User
```bash
python scripts/generate_recommendations.py --user-id user_001 --db-path db/spend_sense.db
```

#### For All Users with Signals
```bash
python scripts/generate_recommendations.py --all --db-path db/spend_sense.db
```

#### Options
- `--user-id`: Generate for specific user ID
- `--all`: Generate for all users with computed signals
- `--db-path`: Database path (default: `db/spend_sense.db`)
- `--max-recs`: Maximum recommendations per user (default: 5)

### How It Works

1. **Fetches User Signals**: Retrieves computed signals from `user_signals` table (180-day window)
2. **Classifies Persona**: Uses `PersonaClassifier` to determine user's financial persona
3. **Maps to Triggers**: Converts signals to `SignalTrigger` enums (e.g., `HIGH_CREDIT_UTILIZATION`)
4. **Filters Content**: Matches content from catalog based on persona and triggers
5. **Scores & Ranks**: Prioritizes content by relevance, persona match, and trigger alignment
6. **Generates Rationales**: Creates human-readable explanations for each recommendation
7. **Saves to Database**: Stores recommendations with `rec_id`, `user_id`, `content_id`, and `rationale`

### Checking Existing Recommendations

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('db/spend_sense.db')
conn.row_factory = sqlite3.Row
recs = conn.execute('SELECT user_id, COUNT(*) as count FROM recommendations GROUP BY user_id').fetchall()
for row in recs:
    print(f'{row[\"user_id\"]}: {row[\"count\"]} recommendations')
conn.close()
"
```

### Viewing Recommendations in UI

1. Start Streamlit dashboard:
   ```bash
   streamlit run src/ui/streamlit_app.py
   ```

2. Navigate to "User View" page
3. Enter user ID (e.g., `user_001`) or click from the list
4. Recommendations will appear in the "💡 Recommendations for You" section

### Current Status

**Users with Recommendations:**
- `smoke_test_user`: 5 recommendations
- `test_user`: 5 recommendations
- `user_001`: 5 recommendations (added 2025-11-07)

**Content Catalog:**
- 28 content items available
- Covers personas: high_utilization, variable_income, subscription_heavy, savings_builder, fee_fighter, fraud_risk

### Troubleshooting

**No recommendations generated:**
- Check if user has signals: `SELECT * FROM user_signals WHERE user_id = 'user_001'`
- Verify persona classification: User may have `insufficient_data` persona
- Check content catalog: Ensure `data/content/catalog.json` exists and is valid

**Recommendations not showing in UI:**
- Verify recommendations exist: `SELECT * FROM recommendations WHERE user_id = 'user_001'`
- Check database path: Ensure `db_path` in session state matches actual database location
- Refresh Streamlit page or clear browser cache

**Recommendations seem generic:**
- User may have low data quality score
- Persona classification may be `insufficient_data`
- Consider computing signals with more transaction history

### Next Steps

When picking up work:
1. Check which users need recommendations: Query `user_signals` vs `recommendations` tables
2. Generate recommendations for new users or users without recommendations
3. Test in UI: Load user profiles and verify recommendations display correctly
4. Review recommendation quality: Check rationales make sense for user's persona

### Related Files

- **Script**: `scripts/generate_recommendations.py`
- **Engine**: `src/recommend/recommendation_engine.py`
- **Content Catalog**: `data/content/catalog.json`
- **Persona Config**: `config/personas.yaml`
- **Signal Mapper**: `src/recommend/signal_mapper.py`

