-- SpendSense Database Schema
-- Version: 3.0
-- CRITICAL: Field names must align with UserSignals schema

-- Users table
CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    consent_status BOOLEAN DEFAULT FALSE,
    consent_date TIMESTAMP
);

-- Accounts (Plaid-style structure)
CREATE TABLE accounts (
    account_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,  -- checking, savings, credit card, investment
    subtype TEXT,        -- checking, savings, credit card, etc.
    available_balance REAL,
    current_balance REAL,
    credit_limit REAL,
    iso_currency_code TEXT DEFAULT 'USD',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Transactions
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    amount REAL NOT NULL,  -- Positive for inflow, negative for outflow
    merchant_name TEXT,
    category_primary TEXT,
    category_detailed TEXT,
    payment_channel TEXT,  -- online, in store, atm, other
    pending BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Credit card details
CREATE TABLE liabilities (
    account_id TEXT PRIMARY KEY,
    apr_percentage REAL,
    minimum_payment_amount REAL,
    last_payment_amount REAL,
    is_overdue BOOLEAN DEFAULT FALSE,
    next_payment_due_date DATE,
    last_statement_balance REAL,
    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- Computed signals (cached for performance)
CREATE TABLE user_signals (
    user_id TEXT NOT NULL,
    window TEXT NOT NULL,  -- '30d' or '180d'
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    signals JSON NOT NULL,  -- UserSignals as JSON
    PRIMARY KEY (user_id, window),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Persona assignments
CREATE TABLE persona_assignments (
    user_id TEXT NOT NULL,
    window TEXT NOT NULL,
    persona TEXT NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    criteria JSON NOT NULL,  -- Matched criteria for explainability
    PRIMARY KEY (user_id, window),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Recommendations
CREATE TABLE recommendations (
    rec_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    content_id TEXT NOT NULL,
    rationale TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved BOOLEAN DEFAULT NULL,  -- NULL=pending, TRUE=approved, FALSE=rejected
    delivered BOOLEAN DEFAULT FALSE,
    viewed_at TIMESTAMP,  -- For content deduplication
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Create indexes for performance
CREATE INDEX idx_transactions_user_date ON transactions(user_id, date);
CREATE INDEX idx_transactions_merchant ON transactions(merchant_name);
CREATE INDEX idx_accounts_user_type ON accounts(user_id, type);
CREATE INDEX idx_recommendations_user_created ON recommendations(user_id, created_at);

