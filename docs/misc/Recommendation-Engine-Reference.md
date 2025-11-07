# Recommendation Engine Reference

## High-Level Overview

The recommendation engine transforms user financial signals into personalized content recommendations with explainable rationales. It follows a 7-step pipeline:

1. **Persona Classification** - Matches user signals to a financial persona (e.g., "High Utilization", "Variable Income")
2. **Signal Mapping** - Converts numeric signals to categorical triggers (e.g., `credit_utilization_max >= 0.5` → `HIGH_CREDIT_UTILIZATION`)
3. **Content Filtering** - Retrieves content matching persona and triggers from catalog
4. **Deduplication** - Excludes recently viewed content (default: 30 days)
5. **Eligibility Checking** - Validates user meets content requirements (income, credit score, account types)
6. **Scoring & Ranking** - Scores content by relevance and sorts by priority
7. **Rationale Generation** - Creates human-readable "because" explanations for each recommendation

The engine produces a list of `Recommendation` objects, each containing content metadata, a personalized rationale, and match reasons. Recommendations are persisted to the database and can be filtered through guardrails for safety and compliance.

---

## Detailed Implementation

### Core Classes

#### `RecommendationEngine`
Main engine class that orchestrates the recommendation generation process.

**Initialization:**
```python
engine = RecommendationEngine(catalog_path="data/content/catalog.json")
```
- Loads and validates content catalog on initialization
- Catalog contains 20+ content items with persona tags, signal triggers, and eligibility requirements

#### `Recommendation`
Data class representing a single recommendation output:
- `rec_id`: Unique identifier (UUID)
- `content_id`: Reference to content catalog item
- `title`, `description`, `url`: Content metadata
- `type`: Content type (article, checklist, calculator, partner_offer)
- `reading_time_minutes`: Estimated reading time
- `rationale`: Human-readable "because" explanation
- `priority_score`: Calculated relevance score
- `match_reasons`: List of matching criteria (for debugging/transparency)

### Main Method: `generate_recommendations()`

**Signature:**
```python
def generate_recommendations(
    user_id: str,
    signals: UserSignals,
    max_recommendations: int = 5,
    exclude_recent_days: int = 30
) -> List[Recommendation]
```

**Step-by-Step Process:**

#### Step 1: Persona Classification
```python
persona_match = classify_persona(signals)
```
- Evaluates user signals against persona criteria from `config/personas.yaml`
- Criteria use operators: `==`, `!=`, `<`, `<=`, `>`, `>=`
- Supports AND/OR combinators for multi-criteria matching
- Returns `PersonaMatch` with persona_id, confidence, and matched criteria
- Falls back to "insufficient_data" persona if no match or data quality < 0.1

#### Step 2: Signal to Trigger Mapping
```python
triggers = map_signals_to_triggers(signals)
```
- Converts numeric signals to categorical `SignalTrigger` enums
- Examples:
  - `credit_utilization_max >= 0.5` → `HIGH_CREDIT_UTILIZATION`
  - `subscription_count >= 3` → `MANY_SUBSCRIPTIONS`
  - `cash_flow_buffer < 1.0` → `LOW_CASH_BUFFER`
- Returns list of matching triggers (can be multiple)

#### Step 3: Recent Content Deduplication
```python
recent_content_ids = self._get_recent_content_ids(user_id, exclude_recent_days)
```
- Queries `recommendations` table for content viewed in last N days (default: 30)
- Filters by `viewed_at IS NOT NULL` and `viewed_at > cutoff_date`
- Returns list of `content_id`s to exclude

#### Step 4: Content Filtering
```python
candidate_items = self._filter_content(persona_match, triggers)
```
**Method:** `_filter_content(persona_match, triggers) -> List[ContentItem]`
- Gets content matching persona: `catalog.get_by_personas([persona_id])`
- Gets content matching triggers: `catalog.get_by_signals(triggers)`
- Combines both sets and deduplicates by `content_id`
- Returns union of persona-matched and trigger-matched content

#### Step 5: Eligibility Checking & Deduplication
```python
if item.content_id in recent_content_ids:
    continue  # Skip recently viewed

if self._check_eligibility(item, signals, user_id):
    eligible_items.append(item)
```
**Method:** `_check_eligibility(item, signals, user_id) -> bool`
- Checks `item.eligibility` requirements:
  - `min_income`: Minimum annual income (currently not enforced - needs user income data)
  - `min_credit_score`: Minimum credit score (currently not enforced - needs credit score data)
  - `required_account_types`: Required account types like ["credit", "checking"] (currently not enforced)
  - `excluded_products`: Products user shouldn't have (currently not enforced)
  - `max_age_days`: Content expiration (currently assumes all content is fresh)
- Returns `True` if all checks pass (currently always returns `True` - eligibility checks are placeholders)

#### Step 6: Scoring & Ranking
```python
scored_items = self._score_content(eligible_items, persona_match, triggers, signals)
```
**Method:** `_score_content(items, persona_match, triggers, signals) -> List[Tuple[ContentItem, float]]`

**Scoring Algorithm:**
```python
score = item.priority_score  # Base priority (0.0-10.0 from catalog)

# Persona match boost
if persona_match.persona_id in item.personas:
    score += 2.0

# Trigger match boost
matching_triggers = [t for t in triggers if t in item.signal_triggers]
score += len(matching_triggers) * 1.0  # +1.0 per matching trigger

# Confidence boost
score += persona_match.confidence * 1.0  # 0.0-1.0

# Content type preferences
if item.type == ContentType.ARTICLE:
    score += 0.5
elif item.type == ContentType.CHECKLIST:
    score += 0.3
elif item.type == ContentType.PARTNER_OFFER:
    score -= 0.5  # Lower priority for partner offers
```

**Ranking:**
- Sorts by score (descending)
- Returns list of `(ContentItem, score)` tuples

#### Step 7: Rationale Generation
```python
rationale = self._generate_rationale(item, persona_match, triggers, signals)
match_reasons = self._get_match_reasons(item, persona_match, triggers)
```
**Method:** `_generate_rationale(item, persona_match, triggers, signals) -> str`

**Rationale Structure:**
1. Persona-based opening: `"Based on your financial profile ({persona_name.lower()})"`
2. Trigger explanation: `"because {trigger_explanation.lower()}"` (first matching trigger)
3. Specific signal value (if applicable):
   - High utilization: `"your credit utilization is {X}%"`
   - Subscription heavy: `"you have {X} active subscriptions"`
   - Variable income: `"your income gaps are {X} days apart"`

**Example Output:**
```
"Based on your financial profile (high utilization), because your credit card utilization is above 50%, your credit utilization is 75%."
```

**Method:** `_get_match_reasons(item, persona_match, triggers) -> List[str]`
- Returns list of matching criteria for transparency:
  - `"Matches {persona_name} persona"`
  - `"Matches {trigger.value} trigger"` (for each matching trigger)

### Helper Methods

#### `_get_recent_content_ids(user_id, days) -> List[str]`
- Queries database for content viewed in last N days
- SQL: `SELECT DISTINCT content_id FROM recommendations WHERE user_id = ? AND viewed_at > ?`
- Returns list of `content_id`s to exclude

### Persistence

#### `save_recommendations(user_id, recommendations, db_path) -> bool`
- Saves recommendations to `recommendations` table
- Inserts: `rec_id`, `user_id`, `content_id`, `rationale`, `created_at`
- Used by API after generation, before returning to client

### Dependencies

**Input Dependencies:**
- `UserSignals`: Computed financial signals (from signal detection pipeline)
- `ContentCatalog`: Loaded from `data/content/catalog.json` (20+ items)
- `PersonaConfig`: Loaded from `config/personas.yaml` (5 personas with criteria)

**External Modules:**
- `src.personas.persona_classifier`: `classify_persona()`, `PersonaMatch`
- `src.recommend.signal_mapper`: `map_signals_to_triggers()`, `explain_triggers_for_user()`
- `src.recommend.content_schema`: `ContentItem`, `ContentCatalog`, `SignalTrigger`, `load_content_catalog()`
- `src.db.connection`: `database_transaction()` for database queries

**Output:**
- List of `Recommendation` objects (typically 3-5 items)
- Each recommendation includes full content metadata, rationale, and match reasons
- Recommendations are persisted to database and can be filtered through guardrails

### Error Handling

- Returns empty list `[]` on any exception
- Logs errors with context (user_id, error message)
- Gracefully handles missing data (None signals, empty catalog, etc.)
- Persona classification always returns a match (falls back to "insufficient_data")

### Performance Considerations

- Catalog loaded once at initialization (not per-request)
- Database queries are minimal (recent content lookup only)
- Scoring is O(n) where n = number of eligible items
- Typical execution: <100ms for 5 recommendations

