# Phase 2 High-Value Unit Test Opportunities

## Analysis Summary

Phase 2 has **6 critical components** with complex business logic that would benefit from unit tests. The highest-value tests focus on **correctness of core algorithms**, **edge case handling**, and **data integrity** - areas where bugs would cause incorrect recommendations or user experience issues.

**Priority Ranking:**
1. **Persona Classifier** (Critical) - Incorrect persona = wrong recommendations
2. **Signal Mapper** (Critical) - Wrong triggers = mismatched content
3. **Recommendation Engine Scoring** (High) - Incorrect ranking = poor UX
4. **Guardrails** (High) - Safety failures = compliance issues
5. **Content Schema Validation** (Medium) - Catches config errors early
6. **Rationale Generation** (Medium) - Ensures explainability works

---

## 1. Persona Classifier Tests (CRITICAL)

### Why High-Value
- **Business Impact**: Wrong persona = completely wrong recommendations
- **Complexity**: AND/OR logic, multiple criteria, priority tie-breaking
- **Edge Cases**: None values, missing data, multiple matches

### Test Cases

#### Core Functionality
```python
def test_persona_classifier_basic_match():
    """Test basic persona matching with single criterion."""
    signals = UserSignals(credit_utilization_max=0.75)
    match = classify_persona(signals)
    assert match.persona_id == "high_utilization"
    assert match.confidence > 0.0

def test_persona_classifier_and_logic():
    """Test AND combinator - both criteria must match."""
    signals = UserSignals(
        income_pay_gap=50,  # > 45
        cash_flow_buffer=0.5  # < 1.0
    )
    match = classify_persona(signals)
    assert match.persona_id == "variable_income"

def test_persona_classifier_or_logic():
    """Test OR combinator - either criterion can match."""
    signals = UserSignals(
        credit_utilization_max=0.3,  # Doesn't match
        has_interest_charges=True  # Matches
    )
    match = classify_persona(signals)
    assert match.persona_id == "high_utilization"

def test_persona_classifier_priority_tie_breaking():
    """Test that highest priority (lowest number) wins when multiple match."""
    signals = UserSignals(
        credit_utilization_max=0.75,  # Matches high_utilization (priority 1)
        subscription_count=5  # Matches subscription_heavy (priority 3)
    )
    match = classify_persona(signals)
    assert match.persona_id == "high_utilization"  # Priority 1 wins

def test_persona_classifier_insufficient_data_fallback():
    """Test fallback to insufficient_data when no matches."""
    signals = UserSignals(
        credit_utilization_max=0.2,  # Below threshold
        subscription_count=1,  # Below threshold
        insufficient_data=False,
        data_quality_score=0.8
    )
    match = classify_persona(signals)
    assert match.persona_id == "insufficient_data"

def test_persona_classifier_low_data_quality():
    """Test that data_quality_score < 0.1 forces insufficient_data."""
    signals = UserSignals(
        credit_utilization_max=0.75,  # Would match high_utilization
        data_quality_score=0.05  # Too low
    )
    match = classify_persona(signals)
    assert match.persona_id == "insufficient_data"

def test_persona_classifier_none_values():
    """Test handling of None signal values."""
    signals = UserSignals(
        credit_utilization_max=None,  # Should not match
        subscription_count=0
    )
    match = classify_persona(signals)
    # Should fall back to insufficient_data or handle gracefully

def test_persona_classifier_confidence_calculation():
    """Test confidence is calculated correctly based on matched criteria."""
    signals = UserSignals(
        credit_utilization_max=0.75,  # Matches 1 of 3 criteria
        has_interest_charges=False,
        is_overdue=False
    )
    match = classify_persona(signals)
    # Confidence should reflect partial match
    assert 0.0 < match.confidence < 1.0
```

**Value**: Prevents incorrect persona assignment which would cascade to wrong recommendations.

---

## 2. Signal Mapper Tests (CRITICAL)

### Why High-Value
- **Business Impact**: Wrong triggers = content doesn't match user needs
- **Complexity**: Multiple thresholds, edge cases at boundaries
- **Data Integrity**: Must correctly map numeric signals to categorical triggers

### Test Cases

#### Threshold Boundary Tests
```python
def test_signal_mapper_credit_utilization_threshold():
    """Test credit utilization threshold at exactly 0.5."""
    signals_above = UserSignals(credit_utilization_max=0.5)
    signals_below = UserSignals(credit_utilization_max=0.49)
    
    triggers_above = map_signals_to_triggers(signals_above)
    triggers_below = map_signals_to_triggers(signals_below)
    
    assert SignalTrigger.HIGH_CREDIT_UTILIZATION in triggers_above
    assert SignalTrigger.HIGH_CREDIT_UTILIZATION not in triggers_below

def test_signal_mapper_subscription_count_threshold():
    """Test subscription count threshold at exactly 3."""
    signals_at = UserSignals(subscription_count=3)
    signals_below = UserSignals(subscription_count=2)
    
    triggers_at = map_signals_to_triggers(signals_at)
    triggers_below = map_signals_to_triggers(signals_below)
    
    assert SignalTrigger.MANY_SUBSCRIPTIONS in triggers_at
    assert SignalTrigger.MANY_SUBSCRIPTIONS not in triggers_below

def test_signal_mapper_subscription_spend_threshold():
    """Test subscription spend threshold at exactly $50."""
    signals_at = UserSignals(monthly_subscription_spend=50.0)
    signals_below = UserSignals(monthly_subscription_spend=49.99)
    
    triggers_at = map_signals_to_triggers(signals_at)
    triggers_below = map_signals_to_triggers(signals_below)
    
    assert SignalTrigger.HIGH_SUBSCRIPTION_SPEND in triggers_at
    assert SignalTrigger.HIGH_SUBSCRIPTION_SPEND not in triggers_below

def test_signal_mapper_multiple_triggers():
    """Test that multiple triggers can be returned."""
    signals = UserSignals(
        credit_utilization_max=0.75,
        has_interest_charges=True,
        subscription_count=5,
        monthly_subscription_spend=100.0
    )
    triggers = map_signals_to_triggers(signals)
    assert len(triggers) >= 4
    assert SignalTrigger.HIGH_CREDIT_UTILIZATION in triggers
    assert SignalTrigger.HAS_INTEREST_CHARGES in triggers
    assert SignalTrigger.MANY_SUBSCRIPTIONS in triggers
    assert SignalTrigger.HIGH_SUBSCRIPTION_SPEND in triggers

def test_signal_mapper_insufficient_data_fallback():
    """Test that insufficient_data trigger is returned on error."""
    signals = UserSignals(insufficient_data=True)
    triggers = map_signals_to_triggers(signals)
    assert SignalTrigger.INSUFFICIENT_DATA in triggers

def test_signal_mapper_none_values():
    """Test handling of None values in optional fields."""
    signals = UserSignals(
        credit_utilization_max=None,  # Should not trigger
        subscription_count=0
    )
    triggers = map_signals_to_triggers(signals)
    assert SignalTrigger.HIGH_CREDIT_UTILIZATION not in triggers
```

**Value**: Ensures triggers are correctly generated, preventing content mismatches.

---

## 3. Recommendation Engine Scoring Tests (HIGH)

### Why High-Value
- **Business Impact**: Poor ranking = users see less relevant content first
- **Complexity**: Multi-factor scoring with weighted components
- **Edge Cases**: Empty catalogs, no matches, tie scores

### Test Cases

#### Scoring Algorithm
```python
def test_scoring_persona_match_boost():
    """Test that persona match adds +2.0 to score."""
    # Create test content matching persona
    item = ContentItem(...)  # Matches persona
    persona_match = PersonaMatch(persona_id="high_utilization", ...)
    
    scored = engine._score_content([item], persona_match, [], signals)
    base_score = item.priority_score
    final_score = scored[0][1]
    
    assert final_score >= base_score + 2.0

def test_scoring_trigger_match_boost():
    """Test that each matching trigger adds +1.0 to score."""
    triggers = [SignalTrigger.HIGH_CREDIT_UTILIZATION, SignalTrigger.HAS_INTEREST_CHARGES]
    item = ContentItem(signal_triggers=triggers, ...)
    
    scored = engine._score_content([item], persona_match, triggers, signals)
    # Should have +2.0 for 2 matching triggers
    assert scored[0][1] >= item.priority_score + 2.0

def test_scoring_content_type_preferences():
    """Test that articles and checklists are preferred over partner offers."""
    article = ContentItem(type=ContentType.ARTICLE, priority_score=5.0, ...)
    partner = ContentItem(type=ContentType.PARTNER_OFFER, priority_score=5.0, ...)
    
    scored = engine._score_content([article, partner], persona_match, [], signals)
    article_score = next(s[1] for s in scored if s[0].type == ContentType.ARTICLE)
    partner_score = next(s[1] for s in scored if s[0].type == ContentType.PARTNER_OFFER)
    
    assert article_score > partner_score

def test_scoring_ranking_order():
    """Test that items are ranked by score (descending)."""
    items = [ContentItem(priority_score=i, ...) for i in range(5)]
    scored = engine._score_content(items, persona_match, [], signals)
    
    scores = [s[1] for s in scored]
    assert scores == sorted(scores, reverse=True)

def test_scoring_confidence_boost():
    """Test that higher persona confidence boosts score."""
    high_confidence = PersonaMatch(confidence=1.0, ...)
    low_confidence = PersonaMatch(confidence=0.3, ...)
    
    item = ContentItem(priority_score=5.0, ...)
    scored_high = engine._score_content([item], high_confidence, [], signals)
    scored_low = engine._score_content([item], low_confidence, [], signals)
    
    assert scored_high[0][1] > scored_low[0][1]
```

#### Filtering Logic
```python
def test_filter_content_persona_match():
    """Test that content matching persona is included."""
    # Setup catalog with persona-tagged content
    match = classify_persona(signals)
    filtered = engine._filter_content(match, [])
    assert len(filtered) > 0
    assert all(match.persona_id in item.personas for item in filtered)

def test_filter_content_trigger_match():
    """Test that content matching triggers is included."""
    triggers = map_signals_to_triggers(signals)
    filtered = engine._filter_content(persona_match, triggers)
    # Should include content with matching triggers
    assert any(t in item.signal_triggers for item in filtered for t in triggers)

def test_filter_content_deduplication():
    """Test that duplicate content_ids are removed."""
    # Create items with same content_id
    filtered = engine._filter_content(persona_match, triggers)
    content_ids = [item.content_id for item in filtered]
    assert len(content_ids) == len(set(content_ids))
```

**Value**: Ensures most relevant content appears first, improving user experience.

---

## 4. Guardrails Tests (HIGH)

### Why High-Value
- **Business Impact**: Safety failures = compliance violations, user harm
- **Complexity**: Pattern matching, consent checks, rate limiting
- **Edge Cases**: Malformed content, boundary conditions

### Test Cases

#### Consent Checking
```python
def test_guardrails_consent_check_passed():
    """Test consent check when user has consented."""
    # Setup user with consent=True
    assert guardrails.check_consent("user_with_consent") == True

def test_guardrails_consent_check_failed():
    """Test consent check raises GuardrailViolation when no consent."""
    with pytest.raises(GuardrailViolation):
        guardrails.check_consent("user_without_consent")

def test_guardrails_consent_check_missing_user():
    """Test consent check handles missing user gracefully."""
    with pytest.raises(GuardrailViolation):
        guardrails.check_consent("nonexistent_user")
```

#### Content Safety
```python
def test_guardrails_prohibited_pattern_detection():
    """Test that prohibited patterns are detected."""
    content = ContentItem(
        title="You're stupid with money",
        description="...",
        ...
    )
    with pytest.raises(GuardrailViolation):
        guardrails.validate_content_safety(content)

def test_guardrails_positive_framing_enforcement():
    """Test that negative language is rewritten."""
    text = "You can't afford this"
    result = guardrails.enforce_positive_framing(text)
    assert "can't afford" not in result.lower()
    assert "can work toward" in result.lower()

def test_guardrails_disclaimer_injection():
    """Test that disclaimers are injected for partner offers."""
    rec = Recommendation(
        type="partner_offer",
        rationale="This is a great offer"
    )
    filtered = guardrails.filter_recommendations([rec])
    assert "partner offer" in filtered[0].rationale.lower()
    assert "compensation" in filtered[0].rationale.lower()
```

#### Rate Limiting
```python
def test_guardrails_rate_limit_within_limit():
    """Test rate limit check when under limit."""
    # Setup user with < 10 recommendations today
    assert guardrails.check_rate_limit("user_under_limit") == True

def test_guardrails_rate_limit_exceeded():
    """Test rate limit check when exceeded."""
    # Setup user with 10+ recommendations today
    with pytest.raises(GuardrailViolation):
        guardrails.check_rate_limit("user_over_limit")
```

**Value**: Prevents safety and compliance issues that could cause legal problems.

---

## 5. Content Schema Validation Tests (MEDIUM)

### Why High-Value
- **Business Impact**: Invalid catalog = runtime errors, no recommendations
- **Complexity**: Pydantic validation, completeness checks
- **Edge Cases**: Missing fields, invalid personas, duplicate IDs

### Test Cases

```python
def test_content_schema_valid_item():
    """Test that valid content item passes validation."""
    item = ContentItem(
        content_id="test",
        type=ContentType.ARTICLE,
        title="Test Article",
        description="Test description",
        personas=["high_utilization"],
        url="/test"
    )
    assert item.content_id == "test"

def test_content_schema_invalid_persona():
    """Test that invalid persona raises validation error."""
    with pytest.raises(ValueError):
        ContentItem(
            content_id="test",
            type=ContentType.ARTICLE,
            title="Test",
            description="Test",
            personas=["invalid_persona"],  # Should fail
            url="/test"
        )

def test_content_schema_invalid_url():
    """Test that invalid URL format raises error."""
    with pytest.raises(ValueError):
        ContentItem(
            content_id="test",
            type=ContentType.ARTICLE,
            title="Test",
            description="Test",
            personas=["high_utilization"],
            url="invalid-url"  # Should start with http://, https://, or /
        )

def test_content_catalog_completeness():
    """Test catalog completeness validation."""
    catalog = load_content_catalog("data/content/catalog.json")
    issues = catalog.validate_completeness()
    # Should check persona coverage, content type distribution, duplicate IDs
    assert isinstance(issues, list)

def test_content_catalog_persona_coverage():
    """Test that all personas have content."""
    catalog = load_content_catalog("data/content/catalog.json")
    all_personas = {'high_utilization', 'variable_income', 'subscription_heavy', 
                    'savings_builder', 'insufficient_data'}
    covered = set()
    for item in catalog.items:
        covered.update(item.personas)
    assert all_personas.issubset(covered)
```

**Value**: Catches configuration errors early, prevents runtime failures.

---

## 6. Rationale Generation Tests (MEDIUM)

### Why High-Value
- **Business Impact**: Poor rationales = users don't understand recommendations
- **Complexity**: Template generation, signal value interpolation
- **Edge Cases**: Missing signals, empty triggers

### Test Cases

```python
def test_rationale_generation_high_utilization():
    """Test rationale for high utilization persona."""
    signals = UserSignals(credit_utilization_max=0.75)
    persona_match = classify_persona(signals)
    rationale = engine._generate_rationale(item, persona_match, triggers, signals)
    
    assert "high utilization" in rationale.lower()
    assert "75%" in rationale or "credit utilization" in rationale.lower()

def test_rationale_generation_subscription_heavy():
    """Test rationale for subscription heavy persona."""
    signals = UserSignals(subscription_count=5)
    persona_match = classify_persona(signals)
    rationale = engine._generate_rationale(item, persona_match, triggers, signals)
    
    assert "subscription" in rationale.lower()
    assert "5" in rationale

def test_rationale_generation_includes_trigger():
    """Test that rationale includes trigger explanation."""
    triggers = [SignalTrigger.HIGH_CREDIT_UTILIZATION]
    rationale = engine._generate_rationale(item, persona_match, triggers, signals)
    
    assert "because" in rationale.lower()
    assert "credit card utilization" in rationale.lower()

def test_rationale_generation_always_ends_with_period():
    """Test that rationale always ends with period."""
    rationale = engine._generate_rationale(item, persona_match, triggers, signals)
    assert rationale.endswith(".")
```

**Value**: Ensures recommendations are explainable, building user trust.

---

## Integration Test Opportunities

### End-to-End Recommendation Flow
```python
def test_end_to_end_recommendation_generation():
    """Test complete flow from signals to recommendations."""
    signals = UserSignals(
        credit_utilization_max=0.75,
        has_interest_charges=True,
        subscription_count=3
    )
    recommendations = engine.generate_recommendations("test_user", signals)
    
    assert len(recommendations) > 0
    assert all(rec.rationale for rec in recommendations)
    assert all(rec.priority_score > 0 for rec in recommendations)
```

### Persona → Trigger → Content Flow
```python
def test_persona_to_content_matching():
    """Test that persona classification leads to correct content."""
    signals = UserSignals(credit_utilization_max=0.75)
    persona_match = classify_persona(signals)
    triggers = map_signals_to_triggers(signals)
    recommendations = engine.generate_recommendations("test_user", signals)
    
    # All recommendations should match persona or triggers
    assert all(
        persona_match.persona_id in rec.match_reasons[0] or
        any(t.value in str(rec.match_reasons) for t in triggers)
        for rec in recommendations
    )
```

---

## Test Implementation Priority

**Phase 1 (Critical - Implement First):**
1. Persona classifier AND/OR logic tests
2. Signal mapper threshold boundary tests
3. Guardrails consent and safety tests

**Phase 2 (High Value - Implement Next):**
4. Recommendation engine scoring algorithm tests
5. Content filtering and deduplication tests
6. Rationale generation tests

**Phase 3 (Nice to Have):**
7. Content schema validation tests
8. Integration tests
9. Edge case tests (None values, empty data, etc.)

---

## Estimated Test Coverage Impact

- **Current Coverage**: 0% (no tests exist)
- **Target Coverage**: 80%+ of core business logic
- **High-Value Tests**: ~25-30 test cases covering critical paths
- **Estimated Time**: 4-6 hours for comprehensive test suite

**ROI**: High - catches bugs early, prevents incorrect recommendations, ensures safety compliance.

