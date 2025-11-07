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

