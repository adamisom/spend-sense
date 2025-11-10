-- Migration: Add demographic fields to users table
-- Version: 3.1

ALTER TABLE users ADD COLUMN age INTEGER;
ALTER TABLE users ADD COLUMN age_range TEXT;  -- e.g., "18-24", "25-34", "35-44", "45-54", "55-64", "65+"
ALTER TABLE users ADD COLUMN gender TEXT;  -- e.g., "M", "F", "Other", "Prefer not to say"
ALTER TABLE users ADD COLUMN race_ethnicity TEXT;  -- e.g., "White", "Black", "Hispanic", "Asian", "Other"
ALTER TABLE users ADD COLUMN demographic_group TEXT;  -- Combined group for fairness analysis, e.g., "25-34_F_White"

-- Create index for demographic queries
CREATE INDEX idx_users_demographic_group ON users(demographic_group);

