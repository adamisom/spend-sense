-- Migration script to add fraud detection fields to existing databases
-- Run this if you have an existing database that needs to be updated

-- Add new columns to transactions table (if they don't exist)
-- SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so we'll use a try-catch approach
-- In practice, you may want to check if columns exist first

ALTER TABLE transactions ADD COLUMN is_fraud INTEGER DEFAULT 0;
ALTER TABLE transactions ADD COLUMN latitude REAL;
ALTER TABLE transactions ADD COLUMN longitude REAL;
ALTER TABLE transactions ADD COLUMN account_balance REAL;
ALTER TABLE transactions ADD COLUMN transaction_type TEXT;
ALTER TABLE transactions ADD COLUMN amount_category TEXT;
ALTER TABLE transactions ADD COLUMN status TEXT;

-- Create indexes for fraud detection queries
CREATE INDEX IF NOT EXISTS idx_transactions_fraud ON transactions(is_fraud, user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_location ON transactions(latitude, longitude);

