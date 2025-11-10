# Transactions Formatted CSV Integration Plan

## Executive Summary

The `transactions_formatted.csv` file contains 5,000 transactions with 87 fraud cases (1.74% fraud rate). This document outlines how to adapt the SpendSense codebase to leverage this rich dataset, including fraud detection capabilities.

## Key Findings from Analysis

### Data Characteristics
- **5,000 transactions** with 22 columns
- **87 fraud transactions** (1.74% rate)
- **Rich metadata**: geographic (lat/long), temporal (hour, day_of_week), account balance
- **Different schema** from existing `transactions.csv`

### Fraud Patterns
- **89.7% of fraud is approved** (78 transactions) - suggests sophisticated fraud
- **Credit cards** are most common fraud payment method (43.7%)
- **Retail, transportation, gas stations** are top fraud categories
- **Purchases** account for 59.8% of fraud transactions

## Schema Mapping Strategy

### Core Mapping (Required for Compatibility)

| New CSV Field | Existing Schema | Transformation |
|--------------|----------------|----------------|
| `customer_id` | `user_id` | Direct mapping (assume 1:1 or create lookup) |
| `customer_id` | `account_id` | Generate: `{customer_id}_checking` (or derive from data) |
| `merchant_id` | `merchant_name` | Use merchant_id as name, or create lookup table |
| `merchant_category` | `category_primary` | Direct mapping |
| `merchant_category` | `category_detailed` | Same as category_primary, or enhance |
| `payment_method` | `payment_channel` | Map: `debit_card/credit_card` → "in store", `digital_wallet` → "online", `cash` → "other", `bank_transfer` → "other" |
| `status == "pending"` | `pending` | Boolean conversion |
| `amount` | `amount` | Direct mapping (already numeric) |
| `date` | `date` | Direct mapping |

### New Fields to Add

| Field | Type | Purpose |
|-------|------|---------|
| `is_fraud` | INTEGER | Fraud label (0/1) |
| `latitude` | REAL | Geographic location |
| `longitude` | REAL | Geographic location |
| `account_balance` | REAL | Balance at transaction time |
| `transaction_type` | TEXT | purchase, transfer, refund, etc. |
| `amount_category` | TEXT | small, medium, large, very_large, extra_large |
| `status` | TEXT | approved, declined, pending |

## Implementation Plan

### Phase 1: Database Schema Updates

**File**: `db/schema.sql`

```sql
-- Add new columns to transactions table
ALTER TABLE transactions ADD COLUMN is_fraud INTEGER DEFAULT 0;
ALTER TABLE transactions ADD COLUMN latitude REAL;
ALTER TABLE transactions ADD COLUMN longitude REAL;
ALTER TABLE transactions ADD COLUMN account_balance REAL;
ALTER TABLE transactions ADD COLUMN transaction_type TEXT;
ALTER TABLE transactions ADD COLUMN amount_category TEXT;
ALTER TABLE transactions ADD COLUMN status TEXT;  -- approved, declined, pending

-- Create index for fraud detection queries
CREATE INDEX idx_transactions_fraud ON transactions(is_fraud, user_id);
CREATE INDEX idx_transactions_location ON transactions(latitude, longitude);
```

### Phase 2: Data Transformation Module

**New File**: `src/ingest/transaction_transformer.py`

```python
"""
Transform transactions_formatted.csv schema to SpendSense schema
"""
import pandas as pd
from typing import Dict, Any, List

def transform_formatted_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform transactions_formatted.csv to SpendSense schema.
    
    Args:
        df: DataFrame with transactions_formatted.csv schema
        
    Returns:
        DataFrame with SpendSense schema
    """
    transformed = pd.DataFrame()
    
    # Core mappings
    transformed['transaction_id'] = df['transaction_id']
    transformed['user_id'] = df['customer_id']
    transformed['account_id'] = df['customer_id'] + '_checking'  # Default account
    transformed['date'] = pd.to_datetime(df['date']).dt.date
    transformed['amount'] = df['amount']
    transformed['merchant_name'] = df['merchant_id']  # Or lookup table
    transformed['category_primary'] = df['merchant_category']
    transformed['category_detailed'] = df['merchant_category']
    transformed['payment_channel'] = df['payment_method'].map({
        'debit_card': 'in store',
        'credit_card': 'in store',
        'digital_wallet': 'online',
        'cash': 'other',
        'bank_transfer': 'other'
    })
    transformed['pending'] = df['status'] == 'pending'
    
    # New fields
    transformed['is_fraud'] = df['is_fraud']
    transformed['latitude'] = df['latitude']
    transformed['longitude'] = df['longitude']
    transformed['account_balance'] = df['account_balance']
    transformed['transaction_type'] = df['transaction_type']
    transformed['amount_category'] = df['amount_category']
    transformed['status'] = df['status']
    
    return transformed
```

### Phase 3: Update Data Loading Script

**File**: `scripts/load_data.py`

Add support for loading `transactions_formatted.csv`:

```python
def load_formatted_transactions(csv_path: str, db_path: str) -> int:
    """Load transactions_formatted.csv with transformation."""
    from src.ingest.transaction_transformer import transform_formatted_transactions
    
    df = pd.read_csv(csv_path)
    transformed = transform_formatted_transactions(df)
    
    with database_transaction(db_path) as conn:
        transformed.to_sql('transactions', conn, if_exists='append', index=False)
        count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    
    return count
```

### Phase 4: Fraud Signal Extraction

**File**: `src/features/schema.py`

Add fraud-related signals to `UserSignals`:

```python
class UserSignals(BaseModel):
    # ... existing fields ...
    
    # Fraud signals
    fraud_transaction_count: int = Field(0, ge=0, description="Number of fraud transactions")
    fraud_rate: float = Field(0.0, ge=0.0, le=1.0, description="Fraction of transactions that are fraud")
    has_fraud_history: bool = Field(False, description="True if user has any fraud transactions")
    fraud_risk_score: float = Field(0.0, ge=0.0, le=1.0, description="Risk score based on fraud patterns")
```

**New File**: `src/features/fraud_detection.py`

```python
"""
Extract fraud-related signals from transactions
"""
from typing import List, Dict, Any
import pandas as pd

def extract_fraud_signals(transactions: pd.DataFrame) -> Dict[str, Any]:
    """
    Extract fraud-related signals from transactions.
    
    Args:
        transactions: DataFrame with transaction data including is_fraud column
        
    Returns:
        Dictionary with fraud signals
    """
    if 'is_fraud' not in transactions.columns:
        return {
            'fraud_transaction_count': 0,
            'fraud_rate': 0.0,
            'has_fraud_history': False,
            'fraud_risk_score': 0.0
        }
    
    fraud_count = transactions['is_fraud'].sum()
    total_count = len(transactions)
    fraud_rate = fraud_count / total_count if total_count > 0 else 0.0
    
    # Simple risk score based on fraud rate and patterns
    risk_score = min(fraud_rate * 10, 1.0)  # Scale to 0-1
    
    return {
        'fraud_transaction_count': int(fraud_count),
        'fraud_rate': fraud_rate,
        'has_fraud_history': fraud_count > 0,
        'fraud_risk_score': risk_score
    }
```

### Phase 5: Fraud Prevention Persona

**File**: `config/personas.yaml`

Add new persona for fraud risk:

```yaml
fraud_risk:
  name: "Fraud Risk"
  description: "Users with fraud transaction history"
  criteria:
    - field: has_fraud_history
      operator: "=="
      value: true
  priority: 10
```

### Phase 6: Fraud Prevention Content

**File**: `data/content/catalog.json`

Add fraud prevention content items:

```json
{
  "content_id": "fraud_prevention_guide",
  "type": "article",
  "title": "Protect Yourself from Fraud",
  "description": "Learn how to spot and prevent fraudulent transactions",
  "personas": ["fraud_risk"],
  "signal_triggers": ["has_fraud_history"],
  "url": "/content/fraud-prevention",
  "reading_time_minutes": 5,
  "priority_score": 9.0
}
```

### Phase 7: Testing Updates

**New File**: `tests/test_fraud_detection.py`

```python
"""
Tests for fraud detection functionality
"""
import pytest
import pandas as pd
from src.features.fraud_detection import extract_fraud_signals

def test_fraud_signal_extraction():
    """Test fraud signal extraction."""
    transactions = pd.DataFrame({
        'transaction_id': ['T1', 'T2', 'T3'],
        'is_fraud': [0, 1, 0],
        'amount': [100, 50, 200]
    })
    
    signals = extract_fraud_signals(transactions)
    
    assert signals['fraud_transaction_count'] == 1
    assert signals['fraud_rate'] == pytest.approx(1/3)
    assert signals['has_fraud_history'] == True
    assert signals['fraud_risk_score'] > 0
```

**Update**: `tests/conftest.py`

Add fixture for fraud transaction data:

```python
@pytest.fixture
def fraud_transactions():
    """Create sample transactions with fraud."""
    return pd.DataFrame({
        'transaction_id': ['TXN001', 'TXN002'],
        'customer_id': ['CUST001', 'CUST001'],
        'amount': [100.0, 50.0],
        'is_fraud': [0, 1],
        'merchant_category': ['retail', 'transportation'],
        'payment_method': ['credit_card', 'debit_card'],
        'status': ['approved', 'approved']
    })
```

## Testing Strategy

### Unit Tests
1. Test schema transformation
2. Test fraud signal extraction
3. Test fraud rate calculations
4. Test recommendation engine with fraud signals

### Integration Tests
1. Test end-to-end flow with fraud data
2. Test fraud prevention recommendations
3. Test persona classification with fraud signals

### Data Quality Tests
1. Validate fraud labels (0/1 only)
2. Validate geographic coordinates
3. Validate transaction types
4. Validate status values

## Migration Path

### Step 1: Add Schema Support (Non-Breaking)
- Add new columns to database schema
- Update schema migration script
- Test with existing data

### Step 2: Add Transformation Layer
- Create `transaction_transformer.py`
- Test transformation logic
- Validate output schema

### Step 3: Add Fraud Signals
- Add fraud fields to `UserSignals`
- Implement fraud detection logic
- Test signal extraction

### Step 4: Add Fraud Content
- Add fraud prevention persona
- Add fraud prevention content
- Test recommendations

### Step 5: Update Tests
- Add fraud test fixtures
- Update integration tests
- Add fraud-specific test cases

## Risk Considerations

1. **Schema Compatibility**: Ensure transformation doesn't break existing code
2. **Data Quality**: Validate fraud labels are accurate
3. **Performance**: Fraud detection queries may be slower
4. **Privacy**: Geographic data requires careful handling

## Success Metrics

1. ✅ Successfully load and transform `transactions_formatted.csv`
2. ✅ Extract fraud signals from transaction data
3. ✅ Generate fraud prevention recommendations
4. ✅ All tests pass with fraud data
5. ✅ No regression in existing functionality

## Next Steps

1. Review and approve this plan
2. Implement Phase 1 (Database Schema)
3. Implement Phase 2 (Transformation)
4. Implement Phase 3 (Data Loading)
5. Implement Phase 4 (Fraud Signals)
6. Implement Phase 5 (Persona & Content)
7. Implement Phase 6 (Testing)
8. Integration testing
9. Documentation updates

