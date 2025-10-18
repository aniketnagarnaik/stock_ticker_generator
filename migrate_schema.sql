-- Migration Script for Render Production Database
-- Fixes schema issues for company_name and status fields

-- Fix 1: Change company_name from VARCHAR(255) to TEXT (unlimited)
ALTER TABLE stocks ALTER COLUMN company_name TYPE TEXT;

-- Fix 2: Increase status field length to handle 'completed_with_errors'
ALTER TABLE refresh_logs ALTER COLUMN status TYPE VARCHAR(50);

-- Verify changes
\d stocks
\d refresh_logs

