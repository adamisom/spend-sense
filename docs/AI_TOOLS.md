# AI Tools Usage Documentation

**Purpose**: Document AI coding assistants and prompts used during development  
**Last Updated**: November 7, 2025

---

## Overview

This project leveraged AI coding assistants to accelerate development while maintaining code quality and architectural consistency. This document records which tools were used, key prompts, and lessons learned.

---

## Tools Used

### 1. Cursor (Primary)
- **Version**: Latest (as of November 2025)
- **Usage**: Primary IDE and coding assistant
- **Features Used**:
  - Code completion and suggestions
  - Inline code generation
  - Refactoring assistance
  - Debugging help

### 2. Claude (via Cursor)
- **Model**: Claude Sonnet 3.5
- **Usage**: Complex logic implementation, architecture decisions
- **When Used**: 
  - Initial project setup and structure
  - Complex algorithm implementation (persona classification, recommendation engine)
  - Documentation generation

### 3. GitHub Copilot (Secondary)
- **Usage**: Code snippet suggestions, boilerplate generation
- **When Used**: 
  - Database schema design
  - API endpoint templates
  - Test case generation

---

## Key Prompts and Use Cases

### 1. Project Initialization

**Prompt**:
```
Create a Python project structure for a financial education recommendation system with:
- FastAPI for REST API
- SQLite database
- Signal detection from transaction data
- Persona classification
- Recommendation engine
- Streamlit operator dashboard

Follow best practices: type hints, Pydantic validation, comprehensive testing.
```

**Result**: 
- Complete project structure
- Database schema design
- Initial API endpoints
- Testing framework setup

**Lessons**: 
- Clear project structure upfront saves time later
- AI excels at boilerplate and structure

---

### 2. Signal Detection Implementation

**Prompt**:
```
Implement signal detection for financial transactions. Detect:
- Credit utilization (highest card utilization)
- Income patterns (pay gaps, variability)
- Subscription spending (count, monthly spend, share of total)
- Savings behavior (growth rate, emergency fund)

Use Pydantic for validation. Handle edge cases (missing data, zero values).
```

**Result**:
- `src/features/schema.py` with UserSignals model
- Signal computation functions
- Edge case handling

**Lessons**:
- AI is good at implementing well-defined algorithms
- Need to review edge cases manually
- Type hints help AI generate better code

---

### 3. Persona Classification Logic

**Prompt**:
```
Implement persona classification with:
- Configurable criteria (YAML-based)
- AND/OR logic combinators
- Priority-based tie-breaking
- Confidence scoring

Support personas: High Utilization, Variable Income, Subscription-Heavy, Savings Builder, Insufficient Data.
```

**Result**:
- `src/personas/persona_classifier.py`
- `config/personas.yaml` structure
- Flexible matching logic

**Lessons**:
- AI helps with complex conditional logic
- Configuration-driven approach works well
- Need to test edge cases (multiple matches, no matches)

---

### 4. Recommendation Engine

**Prompt**:
```
Build recommendation engine with 7-step pipeline:
1. Persona classification
2. Signal to trigger mapping
3. Recent content deduplication
4. Content filtering (persona + triggers)
5. Eligibility checking
6. Scoring and ranking
7. Rationale generation

Generate plain-language rationales using template system with signal value substitution.
```

**Result**:
- `src/recommend/recommendation_engine.py`
- Rationale template system
- Scoring algorithm

**Lessons**:
- AI excels at implementing multi-step pipelines
- Template system for rationales is maintainable
- Need human review for rationale quality

---

### 5. Streamlit Dashboard

**Prompt**:
```
Create Streamlit operator dashboard with:
- System overview with health metrics
- User analytics page (persona distribution, signals)
- Recommendation review page
- Data quality monitoring
- Performance metrics

Use modern UI with charts, tables, and interactive elements.
```

**Result**:
- `src/ui/streamlit_app.py`
- Multiple page components
- Data visualization

**Lessons**:
- AI is great for UI boilerplate
- Need to iterate on UX based on actual usage
- Streamlit makes rapid prototyping easy

---

### 6. Testing

**Prompt**:
```
Generate comprehensive test suite for:
- Signal detection (edge cases, validation)
- Persona classification (all personas, tie-breaking)
- Recommendation engine (filtering, scoring, rationales)
- Guardrails (consent, content safety)

Use pytest. Aim for 80%+ coverage on critical paths.
```

**Result**:
- 125+ unit tests
- Integration tests
- Test fixtures and utilities

**Lessons**:
- AI generates good test structure
- Need to add tests for business logic edge cases
- Test coverage tools help identify gaps

---

### 7. Documentation

**Prompt**:
```
Generate implementation guides similar to existing Phase 1-3 guides:
- Step-by-step tasks
- Code samples
- Validation steps
- Dependencies

For Phase 4A: End-user interface, 5th persona, decision log, README enhancements.
```

**Result**:
- `docs/Implementation-Phase4A.md`
- `docs/Implementation-Phase4B.md`
- `docs/Implementation-Phase4C.md`

**Lessons**:
- AI is excellent at generating structured documentation
- Following existing format ensures consistency
- Documentation helps with handoff and maintenance

---

## Code Generation Examples

### Example 1: API Endpoint

**Prompt**:
```
Create FastAPI endpoint for getting user profile. Include:
- User ID parameter
- Optional window parameter (30d or 180d)
- Return persona, signals, triggers
- Error handling for missing user
```

**Generated Code**:
```python
@app.get("/profile/{user_id}", response_model=ProfileResponse)
async def get_user_profile(user_id: str, window: str = "180d"):
    """Get user profile with persona and signals."""
    try:
        signals = get_user_signals_from_db(user_id, window)
        if not signals:
            raise HTTPException(status_code=404, detail=f"No signals found for user {user_id}")
        
        persona_match = classify_persona(signals)
        triggers = map_signals_to_triggers(signals)
        
        return ProfileResponse(
            user_id=user_id,
            persona={...},
            signals=signals.model_dump(),
            triggers=[t.value for t in triggers]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Quality**: Excellent - includes error handling, type hints, logging

---

### Example 2: Signal Detection

**Prompt**:
```
Detect subscription spending from transactions. Calculate:
- Count of subscriptions (recurring merchants)
- Monthly spend
- Share of total spending

Handle edge cases: no subscriptions, missing merchant names.
```

**Generated Code**:
```python
def detect_subscriptions(transactions: pd.DataFrame) -> dict:
    """Detect subscription spending patterns."""
    if transactions.empty:
        return {
            'subscription_count': 0,
            'monthly_subscription_spend': 0.0,
            'subscription_share': 0.0
        }
    
    # Identify recurring merchants (appears monthly)
    # ... implementation ...
```

**Quality**: Good - handles edge cases, returns structured data

---

## Debugging Assistance

### Example: Persona Classification Bug

**Issue**: Persona not matching when it should

**Prompt**:
```
Debug persona classification. User has:
- credit_utilization_max: 0.75
- has_interest_charges: True

Should match "high_utilization" persona (criteria: utilization >= 0.5 OR has_interest_charges).

But classify_persona() returns None. Check config loading and criteria evaluation.
```

**AI Suggestion**:
- Check YAML config format
- Verify field name matching (credit_utilization_max vs credit_utilization)
- Add debug logging to criteria evaluation
- Check combinator logic (AND vs OR)

**Resolution**: Field name mismatch in config - fixed by aligning with schema

---

## Lessons Learned

### What Worked Well

1. **Structured Prompts**: Clear, specific prompts generate better code
2. **Iterative Refinement**: Start with AI-generated code, then refine
3. **Type Hints**: Help AI understand context and generate better code
4. **Documentation**: AI excels at generating documentation from code
5. **Boilerplate**: AI is excellent at generating repetitive code (API endpoints, tests)

### Challenges

1. **Complex Business Logic**: AI sometimes misses edge cases - need human review
2. **Architecture Decisions**: AI suggests solutions but human judgment needed
3. **Testing**: AI generates test structure but may miss business logic tests
4. **Code Review**: Always review AI-generated code before committing
5. **Context Window**: Long conversations can lose context - break into smaller tasks

### Best Practices

1. **Use AI for Structure**: Let AI create project structure, then fill in details
2. **Review Everything**: Never commit AI code without review
3. **Test Thoroughly**: AI code may have subtle bugs
4. **Document Decisions**: AI can't explain why decisions were made
5. **Iterate**: Use AI for first draft, then refine based on requirements

---

## Impact Assessment

### Development Speed
- **Estimated without AI**: 80-100 hours
- **Actual with AI**: 40-50 hours
- **Time Saved**: ~50%

### Code Quality
- **Test Coverage**: 80%+ (AI helped generate comprehensive tests)
- **Type Safety**: 100% (AI enforces type hints)
- **Documentation**: Comprehensive (AI generated docs)

### Areas Where AI Helped Most
1. Project structure and boilerplate (saved ~10 hours)
2. API endpoint implementation (saved ~8 hours)
3. Test generation (saved ~6 hours)
4. Documentation (saved ~4 hours)

### Areas Requiring Human Expertise
1. Business logic and edge cases
2. Architecture decisions
3. UX/UI design
4. Performance optimization
5. Security considerations

---

## Conclusion

AI coding assistants significantly accelerated development while maintaining code quality. The key is using AI as a powerful tool while maintaining human oversight and judgment for critical decisions.

**Recommendation**: Continue using AI for:
- Boilerplate code generation
- Test case generation
- Documentation
- Refactoring assistance

**Maintain human control for**:
- Architecture decisions
- Business logic implementation
- Code review
- Security considerations

