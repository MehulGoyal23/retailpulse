"""Sales API routes."""

from flask import Blueprint, jsonify, request, current_app

sales_bp = Blueprint("sales", __name__)


def db():
    return current_app.get_db()


@sales_bp.route("/summary")
def summary():
    """Aggregated sales summary across all time."""
    with db().cursor() as cur:
        cur.execute("""
            SELECT
                COUNT(DISTINCT order_id)   AS total_orders,
                COUNT(DISTINCT customer_id) AS total_customers,
                SUM(quantity)              AS total_units,
                ROUND(SUM(revenue)::numeric, 2)  AS total_revenue,
                ROUND(SUM(profit)::numeric, 2)   AS total_profit,
                ROUND(AVG(discount)::numeric * 100, 1) AS avg_discount_pct,
                ROUND(SUM(profit) / NULLIF(SUM(revenue), 0) * 100, 2) AS profit_margin_pct
            FROM sales;
        """)
        row = cur.fetchone()
    return jsonify(dict(row))


@sales_bp.route("/by-region")
def by_region():
    """Sales grouped by region."""
    with db().cursor() as cur:
        cur.execute("""
            SELECT
                region,
                COUNT(DISTINCT order_id)         AS orders,
                ROUND(SUM(revenue)::numeric, 2)  AS revenue,
                ROUND(SUM(profit)::numeric, 2)   AS profit,
                ROUND(SUM(profit) / NULLIF(SUM(revenue), 0) * 100, 2) AS margin_pct
            FROM sales
            GROUP BY region
            ORDER BY revenue DESC;
        """)
        rows = cur.fetchall()
    return jsonify([dict(r) for r in rows])


@sales_bp.route("/by-category")
def by_category():
    """Sales grouped by category and sub_category."""
    with db().cursor() as cur:
        cur.execute("""
            SELECT
                category,
                sub_category,
                COUNT(DISTINCT order_id)         AS orders,
                SUM(quantity)                    AS units,
                ROUND(SUM(revenue)::numeric, 2)  AS revenue,
                ROUND(SUM(profit)::numeric, 2)   AS profit,
                ROUND(SUM(profit) / NULLIF(SUM(revenue), 0) * 100, 2) AS margin_pct
            FROM sales
            GROUP BY category, sub_category
            ORDER BY revenue DESC;
        """)
        rows = cur.fetchall()
    return jsonify([dict(r) for r in rows])


@sales_bp.route("/timeseries")
def timeseries():
    """Monthly revenue and profit trend."""
    granularity = request.args.get("granularity", "month")
    trunc = "month" if granularity != "year" else "year"

    with db().cursor() as cur:
        cur.execute(f"""
            SELECT
                DATE_TRUNC('{trunc}', order_date)::DATE AS period,
                ROUND(SUM(revenue)::numeric, 2)         AS revenue,
                ROUND(SUM(profit)::numeric, 2)          AS profit,
                COUNT(DISTINCT order_id)                AS orders
            FROM sales
            GROUP BY 1
            ORDER BY 1;
        """)
        rows = cur.fetchall()
    return jsonify([dict(r) for r in rows])


@sales_bp.route("/by-segment")
def by_segment():
    """Sales grouped by customer segment."""
    with db().cursor() as cur:
        cur.execute("""
            SELECT
                segment,
                COUNT(DISTINCT customer_id)      AS customers,
                COUNT(DISTINCT order_id)         AS orders,
                ROUND(SUM(revenue)::numeric, 2)  AS revenue,
                ROUND(SUM(profit)::numeric, 2)   AS profit
            FROM sales
            WHERE segment IS NOT NULL
            GROUP BY segment
            ORDER BY revenue DESC;
        """)
        rows = cur.fetchall()
    return jsonify([dict(r) for r in rows])
