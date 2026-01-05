-- Initial Database Schema
-- This file represents the complete database schema as of 2026-01-02
-- Run this file to initialize a fresh database

-- Create update_updated_at_column function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Companies Table
-- ============================================
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    name_en VARCHAR(255),
    country VARCHAR(100),
    is_active BOOLEAN,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_companies_id ON companies(id);

-- ============================================
-- Source URLs Table
-- ============================================
CREATE TABLE source_urls (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    url VARCHAR(500) NOT NULL,
    url_type VARCHAR(50),
    is_active BOOLEAN,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    CONSTRAINT source_urls_company_id_fkey FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE INDEX ix_source_urls_id ON source_urls(id);
CREATE INDEX idx_source_urls_company_id_active ON source_urls(company_id, is_active);

-- ============================================
-- Articles Table
-- ============================================
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    summary TEXT,
    url VARCHAR(500) NOT NULL UNIQUE,
    published_date DATE,
    category VARCHAR(100),
    business_area VARCHAR(100),
    tags VARCHAR(500),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    is_inappropriate BOOLEAN DEFAULT FALSE NOT NULL,
    inappropriate_reason TEXT,
    is_reviewed BOOLEAN DEFAULT FALSE NOT NULL,
    CONSTRAINT articles_company_id_fkey FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Add comment
COMMENT ON COLUMN articles.is_inappropriate IS 'Flag to mark inappropriate articles that should be excluded from display and analysis';

-- Create indexes
CREATE INDEX ix_articles_id ON articles(id);
CREATE INDEX idx_articles_company_id_published_date ON articles(company_id, published_date DESC);
CREATE INDEX idx_articles_created_at ON articles(created_at DESC);
CREATE INDEX idx_articles_is_inappropriate ON articles(is_inappropriate);

-- ============================================
-- Job Histories Table
-- ============================================
CREATE TABLE job_histories (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITHOUT TIME ZONE,
    total_companies INTEGER,
    processed_companies INTEGER,
    total_articles INTEGER,
    error_message TEXT
);

CREATE INDEX ix_job_histories_id ON job_histories(id);
CREATE INDEX idx_job_histories_status_started_at ON job_histories(status, started_at DESC);

-- ============================================
-- Schedule Settings Table
-- ============================================
CREATE TABLE schedule_settings (
    id SERIAL PRIMARY KEY,
    search_start_date DATE NOT NULL,
    search_end_date DATE NOT NULL,
    schedule_type VARCHAR(50),
    schedule_day INTEGER,
    schedule_hour INTEGER,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE INDEX ix_search_settings_id ON schedule_settings(id);

-- Add trigger for updated_at
CREATE TRIGGER update_search_settings_updated_at
    BEFORE UPDATE ON schedule_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Global Search Settings Table
-- ============================================
CREATE TABLE global_search_settings (
    id SERIAL PRIMARY KEY,
    default_region VARCHAR(10),
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
);

-- Add triggers for updated_at
CREATE TRIGGER update_global_search_settings_updated_at
    BEFORE UPDATE ON global_search_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_search_settings_updated_at
    BEFORE UPDATE ON global_search_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Company Search Settings Table
-- ============================================
CREATE TABLE company_search_settings (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL UNIQUE,
    region VARCHAR(10),
    custom_keywords TEXT[],
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
    CONSTRAINT fk_company_search_settings_company_id FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    CONSTRAINT uq_company_search_settings_company_id UNIQUE (company_id)
);

-- Add trigger for updated_at
CREATE TRIGGER update_company_search_settings_updated_at
    BEFORE UPDATE ON company_search_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Company Global Search Settings Table (Legacy - May be deprecated)
-- ============================================
CREATE TABLE company_global_search_settings (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL UNIQUE,
    region VARCHAR(10),
    custom_keywords TEXT[],
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW() NOT NULL
);
