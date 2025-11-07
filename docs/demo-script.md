# SpendSense Demo Script

**Duration**: 5-10 minutes  
**Audience**: Technical reviewers, stakeholders  
**Goal**: Demonstrate core functionality and value proposition

---

## Introduction (30 seconds)

"SpendSense is an explainable financial education platform that detects behavioral patterns from transaction data, assigns personas, and delivers personalized recommendations with clear rationales. Let me show you how it works."

---

## Part 1: Data Generation & Signal Detection (1 minute)

**What to show**:
1. Open terminal/command line
2. Run data generation: `python -m src.ingest.data_generator --users 50`
3. Show generated CSV files in `data/synthetic/`
4. Explain: "We generate realistic synthetic financial data for 50 users"

**Key points**:
- Synthetic data includes transactions, accounts, liabilities
- Realistic patterns (subscriptions, credit usage, income variability)
- No real financial data (compliance-friendly)

**Script**:
"First, we generate synthetic financial data. This simulates real user transactions while maintaining privacy. The system detects behavioral signals like high credit utilization, subscription spending, and income patterns."

---

## Part 2: API Demonstration (2 minutes)

**What to show**:
1. Start API server: `uvicorn src.api.routes:app --reload`
2. Show API docs: `http://localhost:8000/docs`
3. Make API calls:
   - `GET /health` - System status
   - `GET /profile/user_001` - User profile with persona
   - `GET /recommendations/user_001` - Personalized recommendations

**Key points**:
- RESTful API design
- Clear response format with rationales
- Persona assignment explained

**Script**:
"Now let's see the API in action. We can get a user's profile, which includes their assigned persona and detected signals. Then we request recommendations, which come with clear 'because' rationales explaining why each recommendation was made."

**Example API call**:
```bash
curl http://localhost:8000/recommendations/user_001
```

**Show response**:
- Highlight persona assignment
- Show recommendation with rationale
- Explain how rationale uses actual signal values

---

## Part 3: Operator Dashboard (2 minutes)

**What to show**:
1. Start Streamlit: `streamlit run src/ui/streamlit_app.py`
2. Navigate through pages:
   - System Overview: Health metrics
   - User Analytics: Persona distribution, signal insights
   - Recommendation Engine: Approval workflow
   - Data Quality: Quality scores
   - Performance Metrics: System performance

**Key points**:
- Comprehensive operator view
- Approval workflow for recommendations
- Data quality monitoring
- Performance tracking

**Script**:
"The operator dashboard gives internal teams a complete view of the system. They can see user analytics, review recommendations before delivery, monitor data quality, and track system performance."

**Highlight**:
- Approval workflow: Show pending recommendations, approve/reject
- Data quality: Show users with low quality scores
- Persona distribution: Visualize how users are categorized

---

## Part 4: End-User Experience (1 minute)

**What to show**:
1. Navigate to "User View" page in Streamlit
2. Enter user_id: `user_001`
3. Show persona assignment
4. Show recommendations with rationales
5. Highlight user-friendly formatting

**Key points**:
- Simple, accessible interface
- Clear persona explanation
- Actionable recommendations
- Plain-language rationales

**Script**:
"Finally, here's what end-users see. They enter their user ID and immediately see their financial profile and personalized recommendations. Each recommendation includes a clear explanation of why it matters to them, using their actual financial data."

**Highlight**:
- Persona card with icon and description
- Recommendation cards with rationale
- User-friendly language (not technical)

---

## Part 5: Evaluation & Metrics (1 minute)

**What to show**:
1. Run evaluation: `python -m src.evaluation.metrics` (or CLI tool)
2. Show evaluation report
3. Highlight key metrics:
   - Coverage: % of users with recommendations
   - Quality: Rationale quality, diversity
   - Performance: P95 compute time
   - Guardrails: Consent compliance

**Key points**:
- Comprehensive evaluation system
- Measurable success criteria
- Production-ready metrics

**Script**:
"The system includes comprehensive evaluation metrics. We track coverage, quality, performance, and guardrails compliance. This ensures the system meets our success criteria and maintains high standards."

---

## Conclusion (30 seconds)

**Key takeaways**:
1. Explainable: Every recommendation has a clear rationale
2. Personalized: Based on actual behavioral signals
3. Safe: Guardrails ensure compliance and safety
4. Scalable: Designed for production deployment

**Next steps**:
- Beta testing with real users
- Integration with real financial data providers
- Production deployment

---

## Tips for Recording

1. **Screen recording**:
   - Use QuickTime (Mac), OBS, or Loom
   - Record at 1080p minimum
   - Show cursor movements clearly
   - Use zoom for code/terminal text

2. **Audio**:
   - Use good microphone
   - Record in quiet environment
   - Speak clearly and at moderate pace
   - Add background music (optional, low volume)

3. **Editing**:
   - Add title slide with project name
   - Add transitions between sections
   - Highlight important UI elements
   - Add captions for key points

4. **Upload**:
   - Upload to YouTube (unlisted) or Vimeo
   - Include link in submission
   - Keep video under 10 minutes

