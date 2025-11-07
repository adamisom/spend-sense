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
            
            # Create persona config - handle different why_priority field names
            why_priority = (
                persona_data.get('why_priority_1') or 
                persona_data.get('why_priority_2') or 
                persona_data.get('why_priority_3') or 
                persona_data.get('why_priority_4') or 
                persona_data.get('why_fallback') or 
                ''
            )
            
            personas[persona_id] = PersonaConfig(
                name=persona_data['name'],
                priority=persona_data['priority'],
                description=persona_data['description'],
                criteria=criteria,
                focus_areas=persona_data.get('focus_areas', []),
                why_priority=why_priority
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

