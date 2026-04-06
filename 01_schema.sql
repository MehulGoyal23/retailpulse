-- ============================================================
--  RetailPulse — PostgreSQL Schema
--  01_schema.sql
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Sales Table ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sales (
    id            SERIAL PRIMARY KEY,
    order_id      VARCHAR(20)     NOT NULL UNIQUE,
    order_date    DATE            NOT NULL,
    ship_date     DATE,
    region        VARCHAR(50)     NOT NULL,
    state         VARCHAR(50),
    city          VARCHAR(100),
    category      VARCHAR(50)     NOT NULL,
    sub_category  VARCHAR(50),
    product_name  VARCHAR(255)    NOT NULL,
    quantity      INTEGER         NOT NULL CHECK (quantity > 0),
    unit_price    DECIMAL(10,2)   NOT NULL CHECK (unit_price >= 0),
    discount      DECIMAL(4,2)    NOT NULL DEFAULT 0 CHECK (discount BETWEEN 0 AND 1),
    revenue       DECIMAL(12,2)   NOT NULL,
    cost          DECIMAL(12,2)   NOT NULL DEFAULT 0,
    profit        DECIMAL(12,2)   NOT NULL,
    customer_id   VARCHAR(20),
    customer_name VARCHAR(100),
    segment       VARCHAR(30),
    created_at    TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ── Products Table ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    id           SERIAL PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL UNIQUE,
    category     VARCHAR(50)  NOT NULL,
    sub_category VARCHAR(50),
    base_cost    DECIMAL(10,2) NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── Regions Table ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS regions (
    id          SERIAL PRIMARY KEY,
    region_name VARCHAR(50)  NOT NULL UNIQUE,
    country     VARCHAR(50)  NOT NULL DEFAULT 'United States',
    timezone    VARCHAR(50)
);

-- Seed regions
INSERT INTO regions (region_name, timezone) VALUES
    ('East',    'America/New_York'),
    ('West',    'America/Los_Angeles'),
    ('Central', 'America/Chicago'),
    ('South',   'America/Chicago')
ON CONFLICT (region_name) DO NOTHING;

-- ── ETL Audit Log ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS etl_runs (
    id            SERIAL PRIMARY KEY,
    run_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_file   VARCHAR(255),
    rows_loaded   INTEGER     NOT NULL DEFAULT 0,
    rows_rejected INTEGER     NOT NULL DEFAULT 0,
    status        VARCHAR(20) NOT NULL DEFAULT 'success',
    error_msg     TEXT
);
