-- Migration script to add week_number column to rrg_data table
-- This enables historical RRG data storage

-- Add week_number column to rrg_data table
ALTER TABLE rrg_data ADD COLUMN week_number INTEGER NOT NULL DEFAULT 0;

-- Create index on week_number for better query performance
CREATE INDEX idx_rrg_data_week_number ON rrg_data(week_number);

-- Create composite index on symbol and week_number for efficient queries
CREATE INDEX idx_rrg_data_symbol_week ON rrg_data(symbol, week_number);

-- Update existing records to have week_number = 0 (current week)
UPDATE rrg_data SET week_number = 0 WHERE week_number IS NULL;
