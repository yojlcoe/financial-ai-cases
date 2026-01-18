-- Extend URL column length to TEXT
-- Migration: 001_extend_url_column
-- Date: 2026-01-13
-- Purpose: Change articles.url from VARCHAR(500) to TEXT to support long tracking URLs

-- Change articles.url to TEXT
ALTER TABLE articles ALTER COLUMN url TYPE TEXT;

-- Note: This migration is safe to run on existing data
-- All existing VARCHAR(500) values will be automatically converted to TEXT
