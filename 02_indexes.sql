-- ============================================================
--  RetailPulse — Indexes & Materialized Views
--  02_indexes.sql
-- ============================================================

-- ── Sales Indexes ────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_sales_order_date   ON sales (order_date);
CREATE INDEX IF NOT EXISTS idx_sales_region       ON sales (region);
CREATE INDEX IF NOT EXISTS idx_sales_category     ON sales (category);
CREATE INDEX IF NOT EXISTS idx_sales_sub_category ON sales (sub_category);
CREATE INDEX IF NOT EXISTS idx_sales_customer_id  ON sales (customer_id);
CREATE INDEX IF NOT EXISTS idx_sales_segment      ON sales (segment);

-- Composite index for common Tableau filter pattern
CREATE INDEX IF NOT EXISTS idx_sales_date_region  ON sales (order_date, region);
CREATE INDEX IF NOT EXISTS idx_sales_date_cat     ON sales (order_date, category);

-- ── Materialized View: Monthly Revenue Summary ───────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_monthly_revenue AS
SELECT
    DATE_TRUNC('month', order_date)::DATE  AS month,
    region,
    category,
    SUM(revenue)                           AS total_revenue,
    SUM(profit)                            AS total_profit,
    SUM(quantity)                          AS total_units,
    COUNT(DISTINCT order_id)               AS order_count,
    COUNT(DISTINCT customer_id)            AS unique_customers,
    ROUND(SUM(profit) / NULLIF(SUM(revenue), 0) * 100, 2) AS profit_margin_pct
FROM sales
GROUP BY 1, 2, 3
ORDER BY 1 DESC, 2, 3;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_monthly_revenue
    ON mv_monthly_revenue (month, region, category);

-- ── Materialized View: Product Performance ───────────────────────
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_product_performance AS
SELECT
    product_name,
    category,
    sub_category,
    COUNT(DISTINCT order_id)              AS order_count,
    SUM(quantity)                         AS total_units,
    SUM(revenue)                          AS total_revenue,
    SUM(profit)                           AS total_profit,
    AVG(discount)                         AS avg_discount,
    ROUND(SUM(profit) / NULLIF(SUM(revenue), 0) * 100, 2) AS profit_margin_pct
FROM sales
GROUP BY 1, 2, 3
ORDER BY total_revenue DESC;

-- ── Function: Refresh All Materialized Views ─────────────────────
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_revenue;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_product_performance;
    RAISE NOTICE 'Analytics views refreshed at %', NOW();
END;
$$ LANGUAGE plpgsql;
