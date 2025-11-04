# SpendSense Implementation Checklist - Phase 2

## 🎯 Purpose
This document continues the implementation of SpendSense with **Phase 2: Personas & Recommendations**. Each task is actionable and can be completed in 15-60 minutes with clear validation steps.

**Prerequisites**: Phase 1 must be complete (signal detection working).

## 📋 How to Use This Checklist
1. ✅ Complete tasks in the **exact order specified**
2. 🚫 **Never skip dependency validation** - if a task's dependencies aren't met, stop and fix them first
3. ⏱️ **Time estimates are conservative** - experienced developers may be faster
4. 🧪 **Run validation after each task** - catch issues early
5. 🔄 **If validation fails**, fix the issue before proceeding

---

## 🚀 PHASE 2: Personas & Recommendations

**Phase Goal**: End-to-end recommendation engine with rationales  
**Estimated Total Time**: 18-24 hours  
**Success Criteria**: API returns recommendations with "because" rationales, guardrails enforced

---

### 👤 **Phase 2.1: Content Schema & Validation** (2 hours)

#### ✅ Task 2.1.1: Create Content Item Schema (45 min)
**Dependencies**: Phase 1 complete (signal detection working)  
**Deliverable**: `src/recommend/content_schema.py` with Pydantic validation

**Create `src/recommend/content_schema.py`**:
```python
"""
Content catalog schema and validation
CRITICAL: Prevents runtime errors in recommendation engine
"""
from pydantic import BaseModel, validator, Field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime

class ContentType(str, Enum):
    """Types of content items."""
    ARTICLE = "article"
    CHECKLIST = "checklist"
    CALCULATOR = "calculator"
    PARTNER_OFFER = "partner_offer"

class SignalTrigger(str, Enum):
    """Signal triggers that map to user signal values."""
    # Credit-related triggers
    HIGH_CREDIT_UTILIZATION = "high_credit_utilization"  # credit_utilization_max >= 0.5
    HAS_INTEREST_CHARGES = "has_interest_charges"  # has_interest_charges = true
    IS_OVERDUE = "is_overdue"  # is_overdue = true
    MINIMUM_PAYMENT_ONLY = "minimum_payment_only"  # minimum_payment_only = true
    
    # Income-related triggers
    VARIABLE_INCOME = "variable_income"  # income_pay_gap > 45
    LOW_CASH_BUFFER = "low_cash_buffer"  # cash_flow_buffer < 1.0
    HIGH_INCOME_VARIABILITY = "high_income_variability"  # income_variability > 0.3
    
    # Subscription-related triggers
    MANY_SUBSCRIPTIONS = "many_subscriptions"  # subscription_count >= 3
    HIGH_SUBSCRIPTION_SPEND = "high_subscription_spend"  # monthly_subscription_spend >= 50
    HIGH_SUBSCRIPTION_SHARE = "high_subscription_share"  # subscription_share >= 0.10
    
    # Savings-related triggers
    POSITIVE_SAVINGS = "positive_savings"  # monthly_savings_inflow > 0
    NEGATIVE_SAVINGS_GROWTH = "negative_savings_growth"  # savings_growth_rate < 0
    LOW_EMERGENCY_FUND = "low_emergency_fund"  # emergency_fund_months < 3
    
    # Data quality triggers
    INSUFFICIENT_DATA = "insufficient_data"  # insufficient_data = true

class EligibilityRequirements(BaseModel):
    """Requirements for content eligibility."""
    min_income: Optional[float] = Field(None, description="Minimum annual income required")
    min_credit_score: Optional[int] = Field(None, ge=300, le=850, description="Minimum credit score")
    required_account_types: List[str] = Field(default_factory=list, description="Required account types")
    excluded_products: List[str] = Field(default_factory=list, description="Products user shouldn't already have")
    max_age_days: Optional[int] = Field(None, description="Content expires after this many days")

class ContentItem(BaseModel):
    """A single piece of content in the catalog."""
    content_id: str = Field(..., description="Unique identifier for content")
    type: ContentType = Field(..., description="Type of content")
    title: str = Field(..., min_length=5, max_length=200, description="Content title")
    description: str = Field(..., min_length=10, max_length=1000, description="Content description")
    
    # Targeting
    personas: List[str] = Field(..., min_items=1, description="Which personas this content targets")
    signal_triggers: List[SignalTrigger] = Field(default_factory=list, description="Behavioral triggers")
    
    # Content details
    url: str = Field(..., description="URL to access content")
    reading_time_minutes: int = Field(..., ge=1, le=120, description="Estimated reading time")
    difficulty_level: str = Field(default="beginner", description="beginner, intermediate, advanced")
    
    # Business logic
    eligibility: EligibilityRequirements = Field(default_factory=EligibilityRequirements, description="Who can access this")
    priority_score: float = Field(default=1.0, ge=0.0, le=10.0, description="Higher = more important")
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Creation timestamp")
    version: str = Field(default="1.0", description="Content version for deduplication")
    tags: List[str] = Field(default_factory=list, description="Additional tags for categorization")
    
    @validator('personas')
    def validate_personas(cls, v):
        """Ensure all personas are valid."""
        valid_personas = [
            'high_utilization', 'variable_income', 'subscription_heavy', 
            'savings_builder', 'insufficient_data'
        ]
        for persona in v:
            if persona not in valid_personas:
                raise ValueError(f'Invalid persona: {persona}. Must be one of {valid_personas}')
        return v
    
    @validator('url')
    def validate_url(cls, v):
        """Basic URL validation."""
        if not (v.startswith('http://') or v.startswith('https://') or v.startswith('/')):
            raise ValueError('URL must start with http://, https://, or / for relative URLs')
        return v

class ContentCatalog(BaseModel):
    """Complete content catalog with validation."""
    version: str = Field(..., description="Catalog version")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())
    items: List[ContentItem] = Field(..., min_items=1, description="Content items")
    
    def get_by_personas(self, personas: List[str]) -> List[ContentItem]:
        """Get content items matching any of the given personas."""
        return [item for item in self.items if any(p in item.personas for p in personas)]
    
    def get_by_signals(self, signal_triggers: List[SignalTrigger]) -> List[ContentItem]:
        """Get content items matching any of the given signal triggers."""
        return [item for item in self.items if any(s in item.signal_triggers for s in signal_triggers)]
    
    def get_by_type(self, content_type: ContentType) -> List[ContentItem]:
        """Get content items of a specific type."""
        return [item for item in self.items if item.type == content_type]
    
    def validate_completeness(self) -> List[str]:
        """Validate catalog completeness and return issues."""
        issues = []
        
        # Check persona coverage
        all_personas = {'high_utilization', 'variable_income', 'subscription_heavy', 'savings_builder', 'insufficient_data'}
        covered_personas = set()
        for item in self.items:
            covered_personas.update(item.personas)
        
        missing_personas = all_personas - covered_personas
        if missing_personas:
            issues.append(f"Missing content for personas: {missing_personas}")
        
        # Check content type distribution
        type_counts = {}
        for item in self.items:
            type_counts[item.type] = type_counts.get(item.type, 0) + 1
        
        if type_counts.get(ContentType.ARTICLE, 0) < 3:
            issues.append("Should have at least 3 articles")
        
        if type_counts.get(ContentType.PARTNER_OFFER, 0) < 2:
            issues.append("Should have at least 2 partner offers")
        
        # Check for duplicate content IDs
        content_ids = [item.content_id for item in self.items]
        if len(content_ids) != len(set(content_ids)):
            issues.append("Duplicate content IDs found")
        
        return issues

# Content loading and validation functions
def load_content_catalog(catalog_path: str) -> ContentCatalog:
    """Load and validate content catalog from JSON file."""
    import json
    from pathlib import Path
    
    try:
        catalog_file = Path(catalog_path)
        if not catalog_file.exists():
            raise FileNotFoundError(f"Content catalog not found: {catalog_path}")
        
        with open(catalog_file) as f:
            catalog_data = json.load(f)
        
        # Validate against schema
        catalog = ContentCatalog(**catalog_data)
        
        # Check completeness
        issues = catalog.validate_completeness()
        if issues:
            from loguru import logger
            logger.warning(f"Content catalog issues: {issues}")
        
        from loguru import logger
        logger.info(f"Loaded content catalog: {len(catalog.items)} items, version {catalog.version}")
        
        return catalog
        
    except Exception as e:
        from loguru import logger
        logger.error(f"Failed to load content catalog: {e}")
        # Return minimal fallback catalog
        return create_fallback_catalog()

def create_fallback_catalog() -> ContentCatalog:
    """Create minimal fallback catalog when loading fails."""
    fallback_items = [
        ContentItem(
            content_id="fallback_financial_basics",
            type=ContentType.ARTICLE,
            title="Financial Basics: Getting Started",
            description="Essential financial concepts everyone should know",
            personas=["insufficient_data"],
            url="/content/financial-basics",
            reading_time_minutes=10
        ),
        ContentItem(
            content_id="fallback_budgeting_101",
            type=ContentType.CHECKLIST,  
            title="Simple Budgeting Checklist",
            description="5 steps to create your first budget",
            personas=["insufficient_data", "variable_income"],
            url="/content/budgeting-checklist",
            reading_time_minutes=5
        )
    ]
    
    return ContentCatalog(
        version="fallback-1.0",
        items=fallback_items
    )

# Validation utilities
def validate_catalog_file(catalog_path: str) -> bool:
    """Validate a catalog file without fully loading it."""
    try:
        catalog = load_content_catalog(catalog_path)
        issues = catalog.validate_completeness()
        return len(issues) == 0
    except Exception:
        return False
```

**Validation**:
```python
# Test content schema
from src.recommend.content_schema import ContentItem, ContentCatalog, SignalTrigger, ContentType

# Test valid content item
valid_item = ContentItem(
    content_id="test_article",
    type=ContentType.ARTICLE,
    title="Understanding Credit Utilization",
    description="Learn how credit utilization affects your credit score",
    personas=["high_utilization"],
    signal_triggers=[SignalTrigger.HIGH_CREDIT_UTILIZATION],
    url="https://example.com/credit-utilization",
    reading_time_minutes=8
)
print(f"✅ Valid content item created: {valid_item.content_id}")

# Test catalog validation
test_catalog = ContentCatalog(
    version="test-1.0",
    items=[valid_item]
)
issues = test_catalog.validate_completeness()
print(f"✅ Catalog validation issues: {len(issues)}")

# Test invalid persona (should raise error)
try:
    invalid_item = ContentItem(
        content_id="invalid",
        type=ContentType.ARTICLE,
        title="Test",
        description="Test description",
        personas=["invalid_persona"],  # This should fail
        url="/test",
        reading_time_minutes=5
    )
    print("❌ Should have failed validation")
except Exception as e:
    print(f"✅ Correctly caught invalid persona: {e}")
```

**Blockers for**: Content catalog creation

---

#### ✅ Task 2.1.2: Create Signal to Trigger Mapper (30 min)
**Dependencies**: Task 2.1.1, Phase 1 (UserSignals schema)  
**Deliverable**: `src/recommend/signal_mapper.py` for converting signals to triggers

**Create `src/recommend/signal_mapper.py`**:
```python
"""
Map user signals to content triggers
CRITICAL: Bridges numeric signals to categorical content matching
"""
from typing import List, Dict, Any
from src.features.schema import UserSignals
from src.recommend.content_schema import SignalTrigger
from loguru import logger

def map_signals_to_triggers(signals: UserSignals) -> List[SignalTrigger]:
    """Convert numeric user signals to categorical content triggers.
    
    This is the critical bridge between signal detection and content recommendation.
    """
    triggers = []
    
    try:
        # Credit-related triggers
        if signals.credit_utilization_max is not None and signals.credit_utilization_max >= 0.5:
            triggers.append(SignalTrigger.HIGH_CREDIT_UTILIZATION)
        
        if signals.has_interest_charges:
            triggers.append(SignalTrigger.HAS_INTEREST_CHARGES)
        
        if signals.is_overdue:
            triggers.append(SignalTrigger.IS_OVERDUE)
        
        if signals.minimum_payment_only:
            triggers.append(SignalTrigger.MINIMUM_PAYMENT_ONLY)
        
        # Income-related triggers
        if signals.income_pay_gap is not None and signals.income_pay_gap > 45:
            triggers.append(SignalTrigger.VARIABLE_INCOME)
        
        if signals.cash_flow_buffer is not None and signals.cash_flow_buffer < 1.0:
            triggers.append(SignalTrigger.LOW_CASH_BUFFER)
        
        if signals.income_variability is not None and signals.income_variability > 0.3:
            triggers.append(SignalTrigger.HIGH_INCOME_VARIABILITY)
        
        # Subscription-related triggers
        if signals.subscription_count >= 3:
            triggers.append(SignalTrigger.MANY_SUBSCRIPTIONS)
        
        if signals.monthly_subscription_spend >= 50.0:
            triggers.append(SignalTrigger.HIGH_SUBSCRIPTION_SPEND)
        
        if signals.subscription_share >= 0.10:
            triggers.append(SignalTrigger.HIGH_SUBSCRIPTION_SHARE)
        
        # Savings-related triggers
        if signals.monthly_savings_inflow > 0:
            triggers.append(SignalTrigger.POSITIVE_SAVINGS)
        
        if signals.savings_growth_rate is not None and signals.savings_growth_rate < 0:
            triggers.append(SignalTrigger.NEGATIVE_SAVINGS_GROWTH)
        
        if signals.emergency_fund_months is not None and signals.emergency_fund_months < 3.0:
            triggers.append(SignalTrigger.LOW_EMERGENCY_FUND)
        
        # Data quality triggers
        if signals.insufficient_data:
            triggers.append(SignalTrigger.INSUFFICIENT_DATA)
        
        logger.debug(f"Mapped {len(triggers)} triggers from signals: {[t.value for t in triggers]}")
        return triggers
        
    except Exception as e:
        logger.error(f"Error mapping signals to triggers: {e}")
        # Return at least insufficient data trigger as fallback
        return [SignalTrigger.INSUFFICIENT_DATA]

def get_trigger_explanations() -> Dict[SignalTrigger, str]:
    """Get human-readable explanations for each trigger."""
    return {
        # Credit explanations
        SignalTrigger.HIGH_CREDIT_UTILIZATION: "Your credit card utilization is above 50%",
        SignalTrigger.HAS_INTEREST_CHARGES: "You're paying interest charges on credit cards",
        SignalTrigger.IS_OVERDUE: "You have overdue payments",
        SignalTrigger.MINIMUM_PAYMENT_ONLY: "You're making minimum payments only",
        
        # Income explanations
        SignalTrigger.VARIABLE_INCOME: "Your income timing is irregular (gaps over 45 days)",
        SignalTrigger.LOW_CASH_BUFFER: "Your cash flow buffer is less than 1 month of expenses",
        SignalTrigger.HIGH_INCOME_VARIABILITY: "Your income amounts vary significantly",
        
        # Subscription explanations
        SignalTrigger.MANY_SUBSCRIPTIONS: "You have 3 or more active subscriptions",
        SignalTrigger.HIGH_SUBSCRIPTION_SPEND: "You spend $50+ monthly on subscriptions",
        SignalTrigger.HIGH_SUBSCRIPTION_SHARE: "Subscriptions are 10%+ of your total spending",
        
        # Savings explanations
        SignalTrigger.POSITIVE_SAVINGS: "You're actively saving money",
        SignalTrigger.NEGATIVE_SAVINGS_GROWTH: "Your savings balance is decreasing",
        SignalTrigger.LOW_EMERGENCY_FUND: "Your emergency fund covers less than 3 months of expenses",
        
        # Data quality explanations
        SignalTrigger.INSUFFICIENT_DATA: "We need more transaction data to provide personalized recommendations"
    }

def explain_triggers_for_user(triggers: List[SignalTrigger]) -> List[str]:
    """Generate human-readable explanations for a user's triggers."""
    explanations = get_trigger_explanations()
    return [explanations.get(trigger, f"Trigger: {trigger.value}") for trigger in triggers]

# Testing and validation functions
def validate_signal_mapping(test_signals: UserSignals) -> bool:
    """Validate that signal mapping produces expected triggers."""
    try:
        triggers = map_signals_to_triggers(test_signals)
        
        # Should always return at least one trigger
        if not triggers:
            logger.error("Signal mapping returned no triggers")
            return False
        
        # Should return insufficient_data trigger if data quality is poor
        if test_signals.insufficient_data and SignalTrigger.INSUFFICIENT_DATA not in triggers:
            logger.error("Should return insufficient_data trigger for poor quality signals")
            return False
        
        # Should return appropriate credit triggers
        if (test_signals.credit_utilization_max and test_signals.credit_utilization_max >= 0.5 
            and SignalTrigger.HIGH_CREDIT_UTILIZATION not in triggers):
            logger.error("Should return high_credit_utilization trigger")
            return False
        
        logger.info(f"Signal mapping validation passed: {len(triggers)} triggers")
        return True
        
    except Exception as e:
        logger.error(f"Signal mapping validation failed: {e}")
        return False

# Batch processing for multiple users
def map_signals_batch(signals_dict: Dict[str, UserSignals]) -> Dict[str, List[SignalTrigger]]:
    """Map signals to triggers for multiple users."""
    results = {}
    for user_id, signals in signals_dict.items():
        results[user_id] = map_signals_to_triggers(signals)
    return results
```

**Validation**:
```python
# Test signal mapping
from src.recommend.signal_mapper import map_signals_to_triggers, validate_signal_mapping
from src.features.schema import UserSignals
from src.recommend.content_schema import SignalTrigger

# Create test signals
test_signals = UserSignals(
    credit_utilization_max=0.75,  # Should trigger HIGH_CREDIT_UTILIZATION
    has_interest_charges=True,    # Should trigger HAS_INTEREST_CHARGES
    subscription_count=5,         # Should trigger MANY_SUBSCRIPTIONS
    monthly_subscription_spend=85.0,  # Should trigger HIGH_SUBSCRIPTION_SPEND
    monthly_savings_inflow=250.0,     # Should trigger POSITIVE_SAVINGS
    insufficient_data=False,
    data_quality_score=0.8
)

# Test mapping
triggers = map_signals_to_triggers(test_signals)
print(f"✅ Mapped {len(triggers)} triggers: {[t.value for t in triggers]}")

# Verify expected triggers
expected_triggers = [
    SignalTrigger.HIGH_CREDIT_UTILIZATION,
    SignalTrigger.HAS_INTEREST_CHARGES,
    SignalTrigger.MANY_SUBSCRIPTIONS,
    SignalTrigger.HIGH_SUBSCRIPTION_SPEND,
    SignalTrigger.POSITIVE_SAVINGS
]

for expected in expected_triggers:
    if expected in triggers:
        print(f"✅ Found expected trigger: {expected.value}")
    else:
        print(f"❌ Missing expected trigger: {expected.value}")

# Test validation
is_valid = validate_signal_mapping(test_signals)
print(f"✅ Signal mapping validation: {is_valid}")
```

**Blockers for**: Content catalog creation, recommendation engine

---

#### ✅ Task 2.1.3: Create Sample Content Catalog (60 min)
**Dependencies**: Task 2.1.1, Task 2.1.2  
**Deliverable**: `data/content/catalog.json` with 20+ validated content items

**Create `data/content/catalog.json`**:
```json
{
  "version": "1.0",
  "last_updated": "2025-11-03T12:00:00Z",
  "items": [
    {
      "content_id": "credit_utilization_guide",
      "type": "article",
      "title": "Understanding Credit Utilization: The 30% Rule",
      "description": "Learn how credit utilization affects your credit score and practical strategies to reduce it. Includes balance transfer options and payment timing tips.",
      "personas": ["high_utilization"],
      "signal_triggers": ["high_credit_utilization", "has_interest_charges"],
      "url": "/content/credit-utilization-guide",
      "reading_time_minutes": 12,
      "difficulty_level": "beginner",
      "eligibility": {
        "required_account_types": ["credit"]
      },
      "priority_score": 9.0,
      "tags": ["credit", "utilization", "credit_score"]
    },
    {
      "content_id": "debt_paydown_strategy",
      "type": "checklist",
      "title": "5-Step Debt Paydown Strategy",
      "description": "A proven checklist to tackle high-interest debt systematically. Choose between debt avalanche and snowball methods based on your situation.",
      "personas": ["high_utilization"],
      "signal_triggers": ["high_credit_utilization", "has_interest_charges", "minimum_payment_only"],
      "url": "/content/debt-paydown-checklist",
      "reading_time_minutes": 8,
      "difficulty_level": "intermediate",
      "eligibility": {
        "required_account_types": ["credit"]
      },
      "priority_score": 8.5,
      "tags": ["debt", "paydown", "strategy"]
    },
    {
      "content_id": "balance_transfer_calculator",
      "type": "calculator",
      "title": "Balance Transfer Savings Calculator",
      "description": "Calculate potential savings from balance transfers. Compare offers and see how much you could save in interest charges.",
      "personas": ["high_utilization"],
      "signal_triggers": ["high_credit_utilization", "has_interest_charges"],
      "url": "/tools/balance-transfer-calculator",
      "reading_time_minutes": 5,
      "difficulty_level": "beginner",
      "eligibility": {
        "min_credit_score": 600,
        "required_account_types": ["credit"]
      },
      "priority_score": 7.0,
      "tags": ["balance_transfer", "calculator", "savings"]
    },
    {
      "content_id": "clearcard_balance_transfer",
      "type": "partner_offer",
      "title": "ClearCard 0% Balance Transfer Offer",
      "description": "Transfer your high-interest balances to ClearCard with 0% APR for 18 months. No transfer fees for qualified applicants.",
      "personas": ["high_utilization"],
      "signal_triggers": ["high_credit_utilization", "has_interest_charges"],
      "url": "/offers/clearcard-balance-transfer",
      "reading_time_minutes": 3,
      "difficulty_level": "beginner",
      "eligibility": {
        "min_credit_score": 650,
        "min_income": 35000,
        "excluded_products": ["ClearCard"]
      },
      "priority_score": 6.0,
      "tags": ["partner_offer", "balance_transfer", "0_apr"]
    },
    {
      "content_id": "subscription_audit_guide",
      "type": "checklist",
      "title": "The 10-Minute Subscription Audit",
      "description": "Quick checklist to review all your subscriptions, identify unused services, and cancel or downgrade to save money.",
      "personas": ["subscription_heavy"],
      "signal_triggers": ["many_subscriptions", "high_subscription_spend", "high_subscription_share"],
      "url": "/content/subscription-audit",
      "reading_time_minutes": 10,
      "difficulty_level": "beginner",
      "eligibility": {},
      "priority_score": 7.5,
      "tags": ["subscriptions", "audit", "savings"]
    },
    {
      "content_id": "subscription_negotiation",
      "type": "article",
      "title": "How to Negotiate Lower Subscription Rates",
      "description": "Scripts and strategies for negotiating better rates on your existing subscriptions. Includes specific tactics for different service types.",
      "personas": ["subscription_heavy"],
      "signal_triggers": ["high_subscription_spend"],
      "url": "/content/subscription-negotiation",
      "reading_time_minutes": 15,
      "difficulty_level": "intermediate",
      "eligibility": {},
      "priority_score": 6.5,
      "tags": ["subscriptions", "negotiation", "savings"]
    },
    {
      "content_id": "subscription_tracker",
      "type": "calculator",
      "title": "Subscription Spending Tracker",
      "description": "Track all your subscriptions in one place. Get alerts for price increases and renewal dates. Calculate your total monthly cost.",
      "personas": ["subscription_heavy"],
      "signal_triggers": ["many_subscriptions", "high_subscription_spend"],
      "url": "/tools/subscription-tracker",
      "reading_time_minutes": 7,
      "difficulty_level": "beginner",
      "eligibility": {},
      "priority_score": 7.0,
      "tags": ["subscriptions", "tracker", "organization"]
    },
    {
      "content_id": "percentage_based_budgeting",
      "type": "article",
      "title": "Percentage-Based Budgeting for Variable Income",
      "description": "Learn how to budget when your income changes month to month. Use percentages instead of fixed amounts to stay flexible.",
      "personas": ["variable_income"],
      "signal_triggers": ["variable_income", "high_income_variability"],
      "url": "/content/percentage-budgeting",
      "reading_time_minutes": 18,
      "difficulty_level": "intermediate",
      "eligibility": {},
      "priority_score": 8.0,
      "tags": ["budgeting", "variable_income", "gig_economy"]
    },
    {
      "content_id": "emergency_fund_builder",
      "type": "checklist",
      "title": "Emergency Fund Quick-Start Guide",
      "description": "Step-by-step plan to build your emergency fund, even with irregular income. Start with $500 and build up systematically.",
      "personas": ["variable_income"],
      "signal_triggers": ["low_cash_buffer", "low_emergency_fund"],
      "url": "/content/emergency-fund-guide",
      "reading_time_minutes": 12,
      "difficulty_level": "beginner",
      "eligibility": {},
      "priority_score": 9.0,
      "tags": ["emergency_fund", "savings", "financial_security"]
    },
    {
      "content_id": "income_smoothing_strategies",
      "type": "article",
      "title": "Income Smoothing for Freelancers and Gig Workers",
      "description": "Practical strategies to create more predictable cash flow from irregular income. Includes client retainer models and savings strategies.",
      "personas": ["variable_income"],
      "signal_triggers": ["variable_income", "high_income_variability", "low_cash_buffer"],
      "url": "/content/income-smoothing",
      "reading_time_minutes": 20,
      "difficulty_level": "advanced",
      "eligibility": {},
      "priority_score": 7.5,
      "tags": ["freelance", "gig_economy", "cash_flow"]
    },
    {
      "content_id": "high_yield_savings_guide",
      "type": "article",
      "title": "High-Yield Savings Accounts: Earn 10x More",
      "description": "Compare high-yield savings accounts and learn how to maximize your savings growth. Includes current rate comparisons and switching tips.",
      "personas": ["savings_builder"],
      "signal_triggers": ["positive_savings"],
      "url": "/content/high-yield-savings",
      "reading_time_minutes": 14,
      "difficulty_level": "beginner",
      "eligibility": {},
      "priority_score": 6.0,
      "tags": ["savings", "high_yield", "interest_rates"]
    },
    {
      "content_id": "savings_automation_guide",
      "type": "checklist",
      "title": "Automate Your Savings in 15 Minutes",
      "description": "Quick setup guide for automatic savings transfers. Set up multiple goals and pay yourself first without thinking about it.",
      "personas": ["savings_builder"],
      "signal_triggers": ["positive_savings"],
      "url": "/content/automate-savings",
      "reading_time_minutes": 8,
      "difficulty_level": "beginner",
      "eligibility": {
        "required_account_types": ["checking", "savings"]
      },
      "priority_score": 7.5,
      "tags": ["automation", "savings", "goals"]
    },
    {
      "content_id": "investment_basics",
      "type": "article",
      "title": "Beyond Savings: Investment Basics for Beginners",
      "description": "When you're ready to move beyond savings accounts. Introduction to index funds, ETFs, and retirement accounts.",
      "personas": ["savings_builder"],
      "signal_triggers": ["positive_savings"],
      "url": "/content/investment-basics",
      "reading_time_minutes": 25,
      "difficulty_level": "intermediate",
      "eligibility": {
        "min_income": 50000
      },
      "priority_score": 5.5,
      "tags": ["investing", "retirement", "wealth_building"]
    },
    {
      "content_id": "wealthfront_robo_advisor",
      "type": "partner_offer",
      "title": "Wealthfront Automated Investing",
      "description": "Start investing with Wealthfront's robo-advisor. $0 minimum, automated rebalancing, and tax-loss harvesting. First $5,000 managed free.",
      "personas": ["savings_builder"],
      "signal_triggers": ["positive_savings"],
      "url": "/offers/wealthfront-investing",
      "reading_time_minutes": 5,
      "difficulty_level": "beginner",
      "eligibility": {
        "min_income": 40000,
        "excluded_products": ["Wealthfront", "Betterment"]
      },
      "priority_score": 4.0,
      "tags": ["partner_offer", "robo_advisor", "investing"]
    },
    {
      "content_id": "financial_basics_101",
      "type": "article",
      "title": "Financial Basics: Getting Started",
      "description": "Essential financial concepts everyone should know. Budgeting, saving, credit basics, and building healthy money habits.",
      "personas": ["insufficient_data"],
      "signal_triggers": ["insufficient_data"],
      "url": "/content/financial-basics",
      "reading_time_minutes": 16,
      "difficulty_level": "beginner",
      "eligibility": {},
      "priority_score": 8.0,
      "tags": ["basics", "education", "fundamentals"]
    },
    {
      "content_id": "budgeting_101",
      "type": "checklist",
      "title": "Simple Budgeting Checklist",
      "description": "5 steps to create your first budget. Track income, categorize expenses, and set up a simple system that works.",
      "personas": ["insufficient_data", "variable_income"],
      "signal_triggers": ["insufficient_data"],
      "url": "/content/budgeting-101",
      "reading_time_minutes": 10,
      "difficulty_level": "beginner",
      "eligibility": {},
      "priority_score": 8.5,
      "tags": ["budgeting", "basics", "getting_started"]
    },
    {
      "content_id": "overdraft_protection_guide",
      "type": "article",
      "title": "How to Avoid Overdraft Fees",
      "description": "Strategies to prevent overdraft fees and set up proper account monitoring. Includes overdraft protection options and account management tips.",
      "personas": ["variable_income", "insufficient_data"],
      "signal_triggers": ["low_cash_buffer", "variable_income"],
      "url": "/content/avoid-overdraft-fees",
      "reading_time_minutes": 12,
      "difficulty_level": "beginner",
      "eligibility": {
        "required_account_types": ["checking"]
      },
      "priority_score": 7.0,
      "tags": ["overdraft", "fees", "account_management"]
    },
    {
      "content_id": "credit_score_improvement",
      "type": "checklist",
      "title": "30-Day Credit Score Improvement Plan",
      "description": "Step-by-step actions to improve your credit score in 30 days. Focus on quick wins while building long-term habits.",
      "personas": ["high_utilization"],
      "signal_triggers": ["high_credit_utilization", "has_interest_charges"],
      "url": "/content/credit-score-plan",
      "reading_time_minutes": 15,
      "difficulty_level": "intermediate",
      "eligibility": {
        "required_account_types": ["credit"]
      },
      "priority_score": 8.0,
      "tags": ["credit_score", "improvement", "action_plan"]
    },
    {
      "content_id": "side_hustle_tax_guide",
      "type": "article",
      "title": "Tax Tips for Side Hustles and Gig Work",
      "description": "Essential tax considerations for freelancers and gig workers. Deductions, estimated taxes, and record-keeping strategies.",
      "personas": ["variable_income"],
      "signal_triggers": ["variable_income", "high_income_variability"],
      "url": "/content/gig-work-taxes",
      "reading_time_minutes": 22,
      "difficulty_level": "advanced",
      "eligibility": {},
      "priority_score": 6.0,
      "tags": ["taxes", "freelance", "gig_economy"]
    },
    {
      "content_id": "savings_challenge",
      "type": "calculator",
      "title": "52-Week Savings Challenge Calculator",
      "description": "Interactive calculator for the popular 52-week savings challenge. Customize the amounts and track your progress throughout the year.",
      "personas": ["savings_builder", "variable_income"],
      "signal_triggers": ["positive_savings", "low_emergency_fund"],
      "url": "/tools/savings-challenge",
      "reading_time_minutes": 5,
      "difficulty_level": "beginner",
      "eligibility": {},
      "priority_score": 5.0,
      "tags": ["savings", "challenge", "gamification"]
    }
  ]
}
```

**Validation**:
```python
# Test content catalog loading and validation
from src.recommend.content_schema import load_content_catalog, validate_catalog_file

# Test loading
catalog = load_content_catalog("data/content/catalog.json")
print(f"✅ Loaded catalog: {len(catalog.items)} items, version {catalog.version}")

# Test validation
issues = catalog.validate_completeness()
if issues:
    print(f"⚠️  Catalog issues: {issues}")
else:
    print("✅ Catalog validation passed")

# Test persona coverage
personas = ['high_utilization', 'variable_income', 'subscription_heavy', 'savings_builder', 'insufficient_data']
for persona in personas:
    items = catalog.get_by_personas([persona])
    print(f"✅ {persona}: {len(items)} items")

# Test content types
from src.recommend.content_schema import ContentType
for content_type in ContentType:
    items = catalog.get_by_type(content_type)
    print(f"✅ {content_type.value}: {len(items)} items")

# Test file validation
is_valid = validate_catalog_file("data/content/catalog.json")
print(f"✅ File validation: {is_valid}")
```

**Blockers for**: Recommendation engine

---

### 👥 **Phase 2.2: Persona Classification Engine** (2.5 hours)

#### ✅ Task 2.2.1: Create Persona Configuration (30 min)
**Dependencies**: Task 2.1.2 (signal mapping)  
**Deliverable**: `config/personas.yaml` with configurable persona rules

**Create `config/personas.yaml`**:
```yaml
# Persona Configuration
# CRITICAL: Field names must match UserSignals schema exactly

personas:
  high_utilization:
    name: "High Utilization"
    priority: 1  # Highest priority (lowest number)
    description: "Users with high credit card utilization or payment issues"
    criteria:
      - field: "credit_utilization_max"
        operator: ">="
        value: 0.5
        description: "Credit utilization 50% or higher"
      - field: "has_interest_charges"
        operator: "=="
        value: true
        combinator: "OR"
        description: "Currently paying interest charges"
      - field: "is_overdue"
        operator: "=="
        value: true
        combinator: "OR"
        description: "Has overdue payments"
    focus_areas:
      - "utilization_reduction"
      - "payment_planning"
      - "autopay_setup"
      - "debt_consolidation"
    why_priority_1: "Credit issues can spiral quickly and damage long-term financial health"
    
  variable_income:
    name: "Variable Income Budgeter"
    priority: 2
    description: "Users with irregular income patterns and cash flow challenges"
    criteria:
      - field: "income_pay_gap"
        operator: ">"
        value: 45
        description: "Income gaps longer than 45 days"
      - field: "cash_flow_buffer"
        operator: "<"
        value: 1.0
        combinator: "AND"
        description: "Cash flow buffer less than 1 month"
    focus_areas:
      - "percentage_budgets"
      - "emergency_fund"
      - "income_smoothing"
      - "overdraft_protection"
    why_priority_2: "Cash flow problems are time-sensitive and affect daily life"
    
  subscription_heavy:
    name: "Subscription-Heavy"
    priority: 3
    description: "Users with many subscriptions or high subscription spending"
    criteria:
      - field: "subscription_count"
        operator: ">="
        value: 3
        description: "Three or more active subscriptions"
      - field: "monthly_subscription_spend"
        operator: ">="
        value: 50.0
        combinator: "OR"
        description: "Monthly subscription spend $50 or more"
      - field: "subscription_share"
        operator: ">="
        value: 0.10
        combinator: "OR"
        description: "Subscriptions are 10% or more of total spending"
    focus_areas:
      - "subscription_audit"
      - "cancellation_strategies"
      - "negotiation_tips"
      - "usage_tracking"
    why_priority_3: "Cost optimization opportunity, but not urgent"
    
  savings_builder:
    name: "Savings Builder"
    priority: 4
    description: "Users actively saving with good credit management"
    criteria:
      - field: "savings_growth_rate"
        operator: ">="
        value: 0.02
        description: "Positive savings growth rate (2%+ monthly)"
      - field: "monthly_savings_inflow"
        operator: ">="
        value: 200.0
        combinator: "OR"
        description: "Monthly savings inflow of $200 or more"
      - field: "credit_utilization_max"
        operator: "<"
        value: 0.30
        combinator: "AND"
        description: "Credit utilization below 30%"
    focus_areas:
      - "goal_setting"
      - "automation"
      - "apy_optimization"
      - "investment_basics"
    why_priority_4: "Growth opportunity for users already in good financial shape"
    
  insufficient_data:
    name: "Insufficient Data"
    priority: 999  # Fallback priority
    description: "Users with insufficient data for specific recommendations"
    criteria:
      - field: "insufficient_data"
        operator: "=="
        value: true
        description: "Flagged as having insufficient data"
      - field: "data_quality_score"
        operator: "<"
        value: 0.5
        combinator: "OR"
        description: "Data quality score below 50%"
    focus_areas:
      - "financial_basics"
      - "data_connection_guidance"
      - "general_education"
    why_fallback: "Provides general guidance when specific analysis isn't possible"

# Persona assignment settings
assignment_settings:
  # How to handle multiple persona matches
  tie_breaking: "priority"  # Options: priority, first_match, all_matches
  
  # Minimum confidence thresholds
  min_data_quality_score: 0.1  # Below this, always assign insufficient_data
  
  # Logging settings
  log_all_matches: true  # Log all personas that match, not just the assigned one
  
  # Validation settings
  require_at_least_one_match: true  # If no personas match, assign insufficient_data
```

**Create `src/personas/config_loader.py`**:
```python
"""
Load and validate persona configuration
"""
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from loguru import logger

@dataclass
class PersonaCriteria:
    """Single persona matching criterion."""
    field: str
    operator: str  # ==, !=, <, <=, >, >=
    value: Any
    combinator: str = "AND"  # AND, OR
    description: str = ""

@dataclass  
class PersonaConfig:
    """Configuration for a single persona."""
    name: str
    priority: int
    description: str
    criteria: List[PersonaCriteria]
    focus_areas: List[str]
    why_priority: str = ""

def load_persona_config(config_path: str = "config/personas.yaml") -> Dict[str, PersonaConfig]:
    """Load persona configuration from YAML file."""
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"Persona config not found: {config_path}, using defaults")
            return get_default_persona_config()
        
        with open(config_file) as f:
            config_data = yaml.safe_load(f)
        
        personas = {}
        
        for persona_id, persona_data in config_data.get('personas', {}).items():
            # Parse criteria
            criteria = []
            for criterion_data in persona_data.get('criteria', []):
                criteria.append(PersonaCriteria(
                    field=criterion_data['field'],
                    operator=criterion_data['operator'],
                    value=criterion_data['value'],
                    combinator=criterion_data.get('combinator', 'AND'),
                    description=criterion_data.get('description', '')
                ))
            
            # Create persona config
            personas[persona_id] = PersonaConfig(
                name=persona_data['name'],
                priority=persona_data['priority'],
                description=persona_data['description'],
                criteria=criteria,
                focus_areas=persona_data.get('focus_areas', []),
                why_priority=persona_data.get('why_priority_1', persona_data.get('why_priority_2', 
                             persona_data.get('why_priority_3', persona_data.get('why_priority_4',
                             persona_data.get('why_fallback', '')))))
            )
        
        logger.info(f"Loaded {len(personas)} persona configurations from {config_path}")
        return personas
        
    except Exception as e:
        logger.error(f"Failed to load persona config: {e}")
        return get_default_persona_config()

def get_default_persona_config() -> Dict[str, PersonaConfig]:
    """Get default persona configuration as fallback."""
    return {
        'high_utilization': PersonaConfig(
            name="High Utilization",
            priority=1,
            description="Users with high credit utilization",
            criteria=[
                PersonaCriteria("credit_utilization_max", ">=", 0.5, description="High utilization")
            ],
            focus_areas=["utilization_reduction"],
            why_priority="Credit issues are urgent"
        ),
        'insufficient_data': PersonaConfig(
            name="Insufficient Data", 
            priority=999,
            description="Fallback for insufficient data",
            criteria=[
                PersonaCriteria("insufficient_data", "==", True, description="Insufficient data")
            ],
            focus_areas=["financial_basics"],
            why_priority="Fallback persona"
        )
    }

def validate_persona_config(personas: Dict[str, PersonaConfig]) -> List[str]:
    """Validate persona configuration and return issues."""
    issues = []
    
    # Check required personas exist
    required_personas = ['high_utilization', 'insufficient_data']
    for required in required_personas:
        if required not in personas:
            issues.append(f"Missing required persona: {required}")
    
    # Check priority uniqueness (except fallback)
    priorities = [p.priority for p in personas.values() if p.priority < 900]
    if len(priorities) != len(set(priorities)):
        issues.append("Duplicate persona priorities found")
    
    # Check criteria field names (should match UserSignals schema)
    valid_fields = {
        'credit_utilization_max', 'has_interest_charges', 'is_overdue', 'minimum_payment_only',
        'income_pay_gap', 'cash_flow_buffer', 'income_variability',
        'subscription_count', 'monthly_subscription_spend', 'subscription_share',
        'savings_growth_rate', 'monthly_savings_inflow', 'emergency_fund_months',
        'insufficient_data', 'data_quality_score'
    }
    
    for persona_id, persona in personas.items():
        for criterion in persona.criteria:
            if criterion.field not in valid_fields:
                issues.append(f"Invalid field in {persona_id}: {criterion.field}")
    
    return issues
```

**Validation**:
```python
# Test persona configuration loading
from src.personas.config_loader import load_persona_config, validate_persona_config

# Load configuration
personas = load_persona_config("config/personas.yaml")
print(f"✅ Loaded {len(personas)} personas")

# Validate configuration
issues = validate_persona_config(personas)
if issues:
    print(f"⚠️  Configuration issues: {issues}")
else:
    print("✅ Persona configuration validation passed")

# Test persona details
for persona_id, persona in personas.items():
    print(f"✅ {persona_id}: Priority {persona.priority}, {len(persona.criteria)} criteria")
```

**Blockers for**: Persona classifier implementation

---

Continue with Phase 2 tasks...

Would you like me to continue with the remaining Phase 2 tasks (persona classifier, recommendation engine, API endpoints, etc.) or create the Phase 3 document next? This format gives you the same granular, actionable tasks with clear validation steps!
