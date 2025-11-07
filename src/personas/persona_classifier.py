"""
Persona classification engine
Matches user signals to personas based on configurable criteria
"""
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from src.features.schema import UserSignals
from src.personas.config_loader import load_persona_config, PersonaConfig, PersonaCriteria, validate_persona_config

@dataclass
class PersonaMatch:
    """Result of persona matching."""
    persona_id: str
    persona_name: str
    priority: int
    matched_criteria: List[str]  # Descriptions of matched criteria
    confidence: float  # 0.0-1.0, based on how many criteria matched

def evaluate_criterion(signals: UserSignals, criterion: PersonaCriteria) -> bool:
    """Evaluate a single criterion against user signals."""
    try:
        # Get the signal value
        signal_value = getattr(signals, criterion.field, None)
        
        # Handle None values
        if signal_value is None:
            return False
        
        # Evaluate based on operator
        if criterion.operator == "==":
            return signal_value == criterion.value
        elif criterion.operator == "!=":
            return signal_value != criterion.value
        elif criterion.operator == "<":
            return signal_value < criterion.value
        elif criterion.operator == "<=":
            return signal_value <= criterion.value
        elif criterion.operator == ">":
            return signal_value > criterion.value
        elif criterion.operator == ">=":
            return signal_value >= criterion.value
        else:
            logger.warning(f"Unknown operator: {criterion.operator}")
            return False
            
    except Exception as e:
        logger.error(f"Error evaluating criterion {criterion.field}: {e}")
        return False

def evaluate_persona_criteria(signals: UserSignals, persona: PersonaConfig) -> Tuple[bool, List[str]]:
    """Evaluate all criteria for a persona and return (matches, matched_descriptions)."""
    if not persona.criteria:
        return False, []
    
    matched_descriptions = []
    criteria_results = []
    combinators = []
    
    # Evaluate each criterion
    for criterion in persona.criteria:
        result = evaluate_criterion(signals, criterion)
        criteria_results.append(result)
        combinators.append(criterion.combinator)
        
        if result:
            matched_descriptions.append(criterion.description)
    
    # Apply combinators (AND/OR logic)
    if not criteria_results:
        return False, []
    
    # Start with first result
    final_result = criteria_results[0]
    
    # Apply combinators sequentially
    for i in range(1, len(criteria_results)):
        combinator = combinators[i] if i < len(combinators) else "AND"
        
        if combinator == "OR":
            final_result = final_result or criteria_results[i]
        else:  # AND (default)
            final_result = final_result and criteria_results[i]
    
    return final_result, matched_descriptions

def classify_persona(
    signals: UserSignals, 
    config_path: str = "config/personas.yaml",
    tie_breaking: str = "priority"
) -> Optional[PersonaMatch]:
    """Classify user into a persona based on their signals.
    
    Args:
        signals: UserSignals object with computed signals
        config_path: Path to persona configuration YAML
        tie_breaking: How to handle multiple matches ("priority", "first_match", "all_matches")
    
    Returns:
        PersonaMatch object for the assigned persona, or None if no match
    """
    try:
        # Load persona configurations
        personas = load_persona_config(config_path)
        
        # Validate configuration
        issues = validate_persona_config(personas)
        if issues:
            logger.warning(f"Persona config validation issues: {issues}")
        
        # Check data quality threshold first
        # If data quality is too low, assign insufficient_data immediately
        if signals.data_quality_score < 0.1:
            if 'insufficient_data' in personas:
                insufficient_persona = personas['insufficient_data']
                return PersonaMatch(
                    persona_id='insufficient_data',
                    persona_name=insufficient_persona.name,
                    priority=insufficient_persona.priority,
                    matched_criteria=["Data quality score below threshold"],
                    confidence=1.0
                )
        
        # Evaluate all personas
        matches = []
        for persona_id, persona in personas.items():
            matches_persona, matched_descriptions = evaluate_persona_criteria(signals, persona)
            
            if matches_persona:
                # Calculate confidence based on how many criteria matched
                total_criteria = len(persona.criteria)
                matched_count = len(matched_descriptions)
                confidence = matched_count / total_criteria if total_criteria > 0 else 1.0
                
                matches.append(PersonaMatch(
                    persona_id=persona_id,
                    persona_name=persona.name,
                    priority=persona.priority,
                    matched_criteria=matched_descriptions,
                    confidence=confidence
                ))
        
        # Handle no matches - assign insufficient_data as fallback
        if not matches:
            logger.info("No persona matches found, assigning insufficient_data")
            if 'insufficient_data' in personas:
                insufficient_persona = personas['insufficient_data']
                return PersonaMatch(
                    persona_id='insufficient_data',
                    persona_name=insufficient_persona.name,
                    priority=insufficient_persona.priority,
                    matched_criteria=["No specific persona matched"],
                    confidence=0.5
                )
            return None
        
        # Apply tie-breaking logic
        if tie_breaking == "priority":
            # Return persona with highest priority (lowest number)
            best_match = min(matches, key=lambda m: m.priority)
            logger.info(f"Assigned persona: {best_match.persona_id} (priority {best_match.priority})")
            return best_match
        
        elif tie_breaking == "first_match":
            # Return first match (order in config)
            return matches[0]
        
        elif tie_breaking == "all_matches":
            # Return all matches (but we can only return one, so return highest priority)
            best_match = min(matches, key=lambda m: m.priority)
            logger.info(f"Multiple matches found, returning highest priority: {best_match.persona_id}")
            if len(matches) > 1:
                logger.debug(f"All matches: {[m.persona_id for m in matches]}")
            return best_match
        
        else:
            # Default to priority
            best_match = min(matches, key=lambda m: m.priority)
            return best_match
            
    except Exception as e:
        logger.error(f"Error classifying persona: {e}")
        # Return insufficient_data as safe fallback
        try:
            personas = load_persona_config(config_path)
            if 'insufficient_data' in personas:
                insufficient_persona = personas['insufficient_data']
                return PersonaMatch(
                    persona_id='insufficient_data',
                    persona_name=insufficient_persona.name,
                    priority=insufficient_persona.priority,
                    matched_criteria=["Error during classification"],
                    confidence=0.0
                )
        except:
            pass
        return None

def get_all_matching_personas(
    signals: UserSignals,
    config_path: str = "config/personas.yaml"
) -> List[PersonaMatch]:
    """Get all personas that match the user's signals (for analysis/debugging)."""
    try:
        personas = load_persona_config(config_path)
        matches = []
        
        for persona_id, persona in personas.items():
            matches_persona, matched_descriptions = evaluate_persona_criteria(signals, persona)
            
            if matches_persona:
                total_criteria = len(persona.criteria)
                matched_count = len(matched_descriptions)
                confidence = matched_count / total_criteria if total_criteria > 0 else 1.0
                
                matches.append(PersonaMatch(
                    persona_id=persona_id,
                    persona_name=persona.name,
                    priority=persona.priority,
                    matched_criteria=matched_descriptions,
                    confidence=confidence
                ))
        
        return sorted(matches, key=lambda m: m.priority)
        
    except Exception as e:
        logger.error(f"Error getting all matching personas: {e}")
        return []

def save_persona_assignment(
    user_id: str,
    persona_match: PersonaMatch,
    window: str,
    db_path: str = "db/spend_sense.db"
) -> bool:
    """Save persona assignment to database."""
    try:
        from src.db.connection import database_transaction
        import json
        
        with database_transaction(db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO persona_assignments 
                (user_id, window, persona, criteria)
                VALUES (?, ?, ?, ?)
            """, (
                user_id,
                window,
                persona_match.persona_id,
                json.dumps({
                    "matched_criteria": persona_match.matched_criteria,
                    "confidence": persona_match.confidence
                })
            ))
        
        logger.debug(f"Saved persona assignment for user {user_id}: {persona_match.persona_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving persona assignment: {e}")
        return False

