# Transactions Formatted CSV Analysis

## Overview
- **File**: `data/transactions_formatted.csv`
- **Total Transactions**: 5,000
- **Date Range**: 2024-01-01 to 2024-12-31 (full year)
- **Unique Customers**: 191
- **Unique Merchants**: 200
- **Fraud Transactions**: 87 (1.74% fraud rate)
- **Non-Fraud Transactions**: 4,913 (98.26%)
- **Data Quality**: No missing values, no duplicate transaction IDs

## Schema Comparison

### New CSV Schema (transactions_formatted.csv)
```
transaction_id, timestamp, date, time, customer_id, merchant_id, 
merchant_category, transaction_type, payment_method, amount, 
amount_category, status, latitude, longitude, account_balance, 
is_fraud, hour, day_of_week, month, month_name, quarter, year
```

### Existing Schema (transactions.csv)
```
transaction_id, account_id, user_id, date, amount, merchant_name,
category_primary, category_detailed, payment_channel, pending
```

### Key Differences

1. **User/Account Identification**
   - New: `customer_id` (single field)
   - Existing: `user_id` + `account_id` (separate fields)

2. **Merchant Information**
   - New: `merchant_id` (ID only)
   - Existing: `merchant_name` (text name)

3. **Category Structure**
   - New: `merchant_category` (single field: groceries, retail, transportation, etc.)
   - Existing: `category_primary` + `category_detailed` (hierarchical)

4. **Payment Method**
   - New: `payment_method` (debit_card, credit_card, digital_wallet, cash, bank_transfer)
   - Existing: `payment_channel` (online, in store, atm, other)

5. **Transaction Status**
   - New: `status` (approved, declined, pending)
   - Existing: `pending` (boolean)

6. **Additional Fields in New CSV**
   - `timestamp`, `time` - Full datetime information
   - `latitude`, `longitude` - Geographic location
   - `account_balance` - Balance at time of transaction
   - `is_fraud` - Fraud label (0/1)
   - `amount_category` - Categorical amount (small, medium, large, very_large, extra_large)
   - `transaction_type` - purchase, transfer, refund, deposit, withdrawal, fee
   - `hour`, `day_of_week`, `month`, `month_name`, `quarter`, `year` - Temporal features

## Fraud Analysis

### Fraud Distribution
- **Approved**: 78 transactions (89.7%) - Most fraud goes undetected
- **Declined**: 6 transactions (6.9%)
- **Pending**: 3 transactions (3.4%)

### Fraud by Payment Method
- Credit Card: 38 (43.7%) - Most common fraud payment method
- Debit Card: 23 (26.4%)
- Digital Wallet: 15 (17.2%)
- Bank Transfer: 7 (8.0%)
- Cash: 4 (4.6%)

### Fraud by Merchant Category
1. Retail: 13 (14.9%)
2. Transportation: 11 (12.6%)
3. Gas Station: 11 (12.6%)
4. Utilities: 11 (12.6%)
5. Restaurant: 11 (12.6%)
6. Entertainment: 8 (9.2%)
7. Healthcare: 6 (6.9%)
8. Groceries: 6 (6.9%)
9. Online Shopping: 5 (5.7%)
10. Other: 5 (5.7%)

### Fraud by Transaction Type
- Purchase: 52 (59.8%) - Dominant fraud type
- Transfer: 14 (16.1%)
- Refund: 8 (9.2%)
- Deposit: 7 (8.0%)
- Withdrawal: 4 (4.6%)
- Fee: 2 (2.3%)

### Fraud by Amount Category
- Medium: 42 (48.3%)
- Large: 22 (25.3%)
- Very Large: 14 (16.1%)
- Small: 8 (9.2%)
- Extra Large: 1 (1.1%)

### Amount Statistics
- **Fraud Transaction Amounts**:
  - Mean: $76.52
  - Median: $40.16
  - Range: $2.92 to $704.29
- **Non-Fraud Transaction Amounts**:
  - Mean: $65.29
  - Median: $33.06
- **Overall Transaction Amounts**:
  - Mean: $59.14
  - Median: $30.56
  - Std Dev: $113.99
  - Range: $-291.89 to $1,923.29
  - Negative amounts: 794 (15.88%) - refunds, fees, etc.

### Temporal Patterns

#### Fraud by Hour of Day
- Peak hours: 9 AM (9 fraud cases), 15 (3 PM) with 8 cases
- Early morning (2-4 AM): 14 cases (16.1%) - unusual pattern
- Evening (17-23): 20 cases (23.0%)
- Fraud occurs throughout all 24 hours

#### Fraud by Day of Week
- Sunday: 14 (16.1%)
- Wednesday: 13 (14.9%)
- Friday: 13 (14.9%)
- Saturday: 13 (14.9%)
- Thursday: 12 (13.8%)
- Monday: 11 (12.6%)
- Tuesday: 11 (12.6%)
- **Relatively even distribution** - no strong day-of-week pattern

#### Fraud by Month
- August: 12 (13.8%)
- February: 11 (12.6%)
- June: 10 (11.5%)
- November: 9 (10.3%)
- May: 7 (8.0%)
- October: 7 (8.0%)
- March: 6 (6.9%)
- December: 6 (6.9%)
- April: 5 (5.7%)
- July: 5 (5.7%)
- September: 5 (5.7%)
- January: 4 (4.6%)
- Fraud spans **79 unique dates** across the year

### Geographic Analysis
- **All fraud transactions have valid coordinates**
- Latitude range: 37.000281 to 39.999871 (California region)
- Longitude range: -122.999686 to -120.000476
- Geographic clustering could be analyzed for fraud patterns

### Account Balance Analysis
- **Overall account balances**:
  - Mean: $5,087.90
  - Median: $5,109.32
  - Range: $100.08 to $9,999.40
- **Fraud transaction account balances**:
  - Mean: $5,262.34
  - Median: $5,324.76
- Fraud occurs across a wide range of account balances

### Customer-Level Fraud Analysis
- **62 customers (32.46%)** have at least one fraud transaction
- **15 customers** have multiple fraud transactions
- **Top fraud-affected customers**:
  1. CUST000106: 4 fraud transactions (7.1% of their transactions)
  2. CUST000146: 4 fraud transactions (1.7% of their transactions)
  3. CUST000118: 4 fraud transactions (5.6% of their transactions)
  4. CUST000198: 3 fraud transactions (4.6% of their transactions)
  5. CUST000132: 3 fraud transactions (2.5% of their transactions)
- **Pattern**: Some customers are repeat fraud victims

### Merchant-Level Fraud Analysis
- **73 merchants (36.50%)** have at least one fraud transaction
- **Top fraud-affected merchants**:
  1. MERCH000043: 3 fraud transactions (9.7% of transactions)
  2. MERCH000053: 2 fraud transactions (6.9% of transactions)
  3. MERCH000036: 2 fraud transactions (7.7% of transactions)
  4. MERCH000050: 2 fraud transactions (10.0% of transactions)
- **Pattern**: Some merchants have higher fraud rates than others

## Overall Transaction Patterns

### Transaction Types (All Transactions)
- Purchase: 3,190 (63.8%)
- Refund: 515 (10.3%)
- Transfer: 504 (10.1%)
- Fee: 279 (5.6%)
- Deposit: 270 (5.4%)
- Withdrawal: 242 (4.8%)

### Payment Methods (All Transactions)
- Credit Card: 2,074 (41.5%)
- Debit Card: 1,516 (30.3%)
- Digital Wallet: 718 (14.4%)
- Cash: 474 (9.5%)
- Bank Transfer: 218 (4.4%)

### Merchant Categories (All Transactions)
- Other: 560 (11.2%)
- Retail: 535 (10.7%)
- Utilities: 520 (10.4%)
- Healthcare: 512 (10.2%)
- Restaurant: 498 (10.0%)
- Entertainment: 497 (9.9%)
- Groceries: 483 (9.7%)
- Transportation: 476 (9.5%)
- Online Shopping: 460 (9.2%)
- Gas Station: 459 (9.2%)

### Status Distribution (All Transactions)
- Approved: 4,639 (92.8%)
- Declined: 275 (5.5%)
- Pending: 86 (1.7%)

## Key Fraud Insights

1. **High Approval Rate**: 89.7% of fraud transactions are approved, suggesting sophisticated fraud that bypasses detection
2. **Credit Card Dominance**: Credit cards are the most common fraud payment method (43.7%)
3. **Retail Category Risk**: Retail has the highest fraud count (13 cases)
4. **Purchase Transactions**: Most fraud occurs through purchases (59.8%)
5. **Medium Amounts**: Fraud is most common in medium-amount transactions (48.3%)
6. **Early Morning Pattern**: Unusual concentration of fraud in early morning hours (2-4 AM)
7. **Customer Clustering**: 32.46% of customers have fraud, with some having multiple incidents
8. **Merchant Risk**: 36.50% of merchants have fraud, with some showing higher rates
9. **Year-Long Pattern**: Fraud occurs throughout the year with no strong seasonal pattern
10. **Geographic Coverage**: All fraud has valid geographic coordinates for location analysis

## Integration Strategy

### Option 1: Schema Mapping (Recommended)
Create a transformation layer that maps the new schema to the existing schema:

**Mapping Rules:**
- `customer_id` → `user_id` (assume one account per customer, or create synthetic account_id)
- `merchant_id` → `merchant_name` (lookup table or use ID as name)
- `merchant_category` → `category_primary` (direct mapping)
- `merchant_category` → `category_detailed` (same value or more specific)
- `payment_method` → `payment_channel` (map: debit_card/credit_card → "in store", digital_wallet → "online", etc.)
- `status == "pending"` → `pending = True`, else `pending = False`

**New Fields to Store:**
- Add `is_fraud` column to transactions table
- Add `latitude`, `longitude` columns
- Add `account_balance` column
- Add `transaction_type` column
- Consider storing temporal features or computing on-the-fly

### Option 2: Dual Schema Support
Support both schemas with conditional logic based on data source.

### Option 3: Schema Migration
Migrate existing code to use new schema (more invasive).

## Code Adaptations Needed

### 1. Database Schema Updates
```sql
ALTER TABLE transactions ADD COLUMN is_fraud INTEGER DEFAULT 0;
ALTER TABLE transactions ADD COLUMN latitude REAL;
ALTER TABLE transactions ADD COLUMN longitude REAL;
ALTER TABLE transactions ADD COLUMN account_balance REAL;
ALTER TABLE transactions ADD COLUMN transaction_type TEXT;
ALTER TABLE transactions ADD COLUMN amount_category TEXT;
```

### 2. Data Loading Script
- Update `scripts/load_data.py` to handle both schemas
- Add transformation logic for schema mapping
- Handle `customer_id` → `user_id` + `account_id` mapping

### 3. Feature Extraction
- Update signal computation to use new fields
- Consider fraud-related signals (fraud_rate, fraud_risk_score)
- Use geographic data for location-based patterns
- Use temporal features (hour, day_of_week) for spending patterns

### 4. Recommendation Engine
- Add fraud detection content recommendations
- Use fraud patterns to identify at-risk users
- Recommend fraud prevention content

### 5. Testing
- Create test fixtures with fraud data
- Test fraud detection logic
- Test schema transformation
- Test recommendation engine with fraud signals

## Potential Use Cases

### 1. Fraud Detection Signals
- Add `fraud_risk_score` to UserSignals
- Add `fraud_transaction_count` to UserSignals
- Add `fraud_rate` (fraud transactions / total transactions)

### 2. Fraud Prevention Persona
- Create new persona for users with fraud patterns
- Recommend fraud prevention content
- Alert users to suspicious activity

### 3. Geographic Analysis
- Use latitude/longitude for location-based recommendations
- Detect unusual location patterns
- Identify travel vs. local spending

### 4. Temporal Pattern Analysis
- Use hour/day_of_week for spending pattern analysis
- Identify unusual time patterns (fraud indicator)
- Recommend content based on spending time patterns

### 5. Transaction Type Analysis
- Analyze refund patterns
- Analyze transfer patterns
- Use transaction_type for more granular recommendations

## Next Steps

1. **Schema Migration**
   - Update `db/schema.sql` to add new columns
   - Create migration script

2. **Data Transformation**
   - Create `src/ingest/transaction_transformer.py` for schema mapping
   - Update `scripts/load_data.py` to use transformer

3. **Feature Extraction**
   - Update `src/features/` modules to extract fraud signals
   - Add fraud-related signals to `UserSignals` schema

4. **Testing**
   - Create test data with fraud transactions
   - Test fraud detection logic
   - Test recommendation engine with fraud data

5. **Documentation**
   - Update API documentation
   - Update schema documentation
   - Document fraud detection features

