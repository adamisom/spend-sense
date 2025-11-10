"""
Signal output schema - CRITICAL: Field names must match persona criteria exactly
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UserSignals(BaseModel):
    """Standardized signal output schema - field names MUST match persona criteria."""
    
    # Credit signals (CRITICAL: exact field names for persona matching)
    credit_utilization_max: Optional[float] = Field(None, ge=0.0, le=1.0, description="Highest utilization across all cards (0.0-1.0)")
    has_interest_charges: bool = Field(False, description="True if any interest charges detected")
    is_overdue: bool = Field(False, description="True if any overdue payments")
    minimum_payment_only: bool = Field(False, description="True if only making minimum payments")
    
    # Income signals (CRITICAL: exact field names)
    income_pay_gap: Optional[int] = Field(None, ge=0, description="Days between income deposits")
    cash_flow_buffer: Optional[float] = Field(None, ge=0.0, description="Months of expenses covered")
    income_variability: Optional[float] = Field(None, ge=0.0, description="Coefficient of variation")
    
    # Subscription signals (CRITICAL: exact field names)
    subscription_count: int = Field(0, ge=0, description="Number of detected subscriptions")
    monthly_subscription_spend: float = Field(0.0, ge=0.0, description="Total monthly recurring spend")
    subscription_share: float = Field(0.0, ge=0.0, le=1.0, description="Fraction of total spend (0.0-1.0)")
    
    # Savings signals (CRITICAL: exact field names)
    savings_growth_rate: Optional[float] = Field(None, description="Monthly growth rate (can be negative)")
    monthly_savings_inflow: float = Field(0.0, description="Average monthly savings deposits")
    emergency_fund_months: Optional[float] = Field(None, ge=0.0, description="Months of expenses covered")
    
    # Bank fee signals (NEW - for Fee Fighter persona)
    monthly_bank_fees: float = Field(0.0, ge=0.0, description="Total monthly bank fees (overdraft, ATM, maintenance)")
    bank_fee_count: int = Field(0, ge=0, description="Number of bank fee transactions in period")
    has_overdraft_fees: bool = Field(False, description="True if overdraft fees detected")
    has_atm_fees: bool = Field(False, description="True if ATM fees detected")
    has_maintenance_fees: bool = Field(False, description="True if account maintenance fees detected")
    
    # Fraud detection signals (NEW - for fraud prevention)
    fraud_transaction_count: int = Field(0, ge=0, description="Number of fraud transactions in period")
    fraud_rate: float = Field(0.0, ge=0.0, le=1.0, description="Fraction of transactions that are fraud (0.0-1.0)")
    has_fraud_history: bool = Field(False, description="True if user has any fraud transactions")
    fraud_risk_score: float = Field(0.0, ge=0.0, le=1.0, description="Risk score based on fraud patterns (0.0-1.0)")
    
    # Data quality flags
    insufficient_data: bool = Field(False, description="True if below minimum thresholds")
    data_quality_score: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in signals (0.0-1.0)")
    computation_errors: List[str] = Field(default_factory=list, description="Any errors during computation")
    
    # Metadata
    computed_at: datetime = Field(default_factory=datetime.now, description="When signals were computed")
    window: str = Field("180d", description="Time window used ('30d' or '180d')")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SignalValidationError(Exception):
    """Raised when signal validation fails."""
    pass

def validate_signal_completeness(signals: UserSignals) -> List[str]:
    """Validate signal completeness and return list of issues."""
    issues = []
    
    # Check data quality
    if signals.data_quality_score < 0.5:
        issues.append(f"Low data quality score: {signals.data_quality_score}")
    
    # Check for computation errors
    if signals.computation_errors:
        issues.append(f"Computation errors: {signals.computation_errors}")
    
    # Check critical signals for persona assignment
    if signals.credit_utilization_max is None and signals.monthly_savings_inflow == 0:
        issues.append("Neither credit nor savings signals available")
    
    return issues


