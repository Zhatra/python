-- SQL script to create normalized database schema
-- This script creates the companies and charges tables with proper relationships and constraints

-- Create normalized_data schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS normalized_data;

-- Grant permissions on the schema
GRANT ALL PRIVILEGES ON SCHEMA normalized_data TO CURRENT_USER;

-- Create companies table
CREATE TABLE IF NOT EXISTS normalized_data.companies (
    company_id VARCHAR(24) PRIMARY KEY,
    company_name VARCHAR(130) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NULL DEFAULT NULL
);

-- Create charges table with foreign key relationship
CREATE TABLE IF NOT EXISTS normalized_data.charges (
    id VARCHAR(24) PRIMARY KEY,
    company_id VARCHAR(24) NOT NULL,
    amount DECIMAL(16,2) NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NULL DEFAULT NULL,
    
    -- Foreign key constraint
    CONSTRAINT fk_charges_company_id 
        FOREIGN KEY (company_id) 
        REFERENCES normalized_data.companies(company_id)
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
);

-- Create indexes for better query performance

-- Indexes on companies table
CREATE INDEX IF NOT EXISTS idx_company_name 
    ON normalized_data.companies(company_name);

-- Indexes on charges table
CREATE INDEX IF NOT EXISTS idx_charge_company_id 
    ON normalized_data.charges(company_id);

CREATE INDEX IF NOT EXISTS idx_charge_created_at 
    ON normalized_data.charges(created_at);

CREATE INDEX IF NOT EXISTS idx_charge_status 
    ON normalized_data.charges(status);

CREATE INDEX IF NOT EXISTS idx_charge_date_company 
    ON normalized_data.charges(created_at, company_id);

-- Create daily transaction summary view
CREATE OR REPLACE VIEW normalized_data.daily_transaction_summary AS
SELECT 
    DATE(c.created_at) as transaction_date,
    comp.company_name,
    comp.company_id,
    SUM(c.amount) as total_amount,
    COUNT(*)::text as transaction_count
FROM normalized_data.charges c
JOIN normalized_data.companies comp ON c.company_id = comp.company_id
WHERE c.status IN ('paid', 'refunded')
GROUP BY DATE(c.created_at), comp.company_id, comp.company_name
ORDER BY transaction_date DESC, total_amount DESC;

-- Add comments for documentation
COMMENT ON SCHEMA normalized_data IS 'Normalized schema for transaction data with proper relationships';
COMMENT ON TABLE normalized_data.companies IS 'Company information with unique identifiers';
COMMENT ON TABLE normalized_data.charges IS 'Transaction charges linked to companies';
COMMENT ON VIEW normalized_data.daily_transaction_summary IS 'Daily aggregated transaction summary by company';

-- Add column comments
COMMENT ON COLUMN normalized_data.companies.company_id IS 'Unique identifier for the company (max 24 chars)';
COMMENT ON COLUMN normalized_data.companies.company_name IS 'Company name (max 130 chars)';
COMMENT ON COLUMN normalized_data.charges.id IS 'Unique identifier for the charge (max 24 chars)';
COMMENT ON COLUMN normalized_data.charges.company_id IS 'Foreign key reference to companies table';
COMMENT ON COLUMN normalized_data.charges.amount IS 'Transaction amount with 2 decimal precision';
COMMENT ON COLUMN normalized_data.charges.status IS 'Transaction status (paid, pending_payment, voided, refunded, pre_authorized, charged_back)';