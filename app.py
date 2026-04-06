"""
RetailPulse — Flask REST API
Serves analytics data to Tableau and other clients.
"""

import os
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, g
from flask_cors import CORS

from routes.sales    import sales_bp
from routes.products import products_bp
from routes.regions  import regions_bp

app = Flask(__name__)
CORS(app)

# ── Database helpers ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("POSTGRES_HOST", "localhost"),
    "port":     int(os.getenv("POSTGRES_PORT", 5432)),
    "dbname":   os.getenv("POSTGRES_DB", "retailpulse"),
    "user":     os.getenv("POSTGRES_USER", "retailuser"),
    "password": os.getenv("POSTGRES_PASSWORD", "changeme"),
}


def get_db():
    if "db" not in g:
        g.db = psycopg2.connect(
            **DB_CONFIG,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


app.get_db = get_db


# ── Blueprints ───────────────────────────────────────────────────
app.register_blueprint(sales_bp,    url_prefix="/api/sales")
app.register_blueprint(products_bp, url_prefix="/api/products")
app.register_blueprint(regions_bp,  url_prefix="/api/regions")


# ── Health check ─────────────────────────────────────────────────
@app.route("/api/health")
def health():
    try:
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS cnt FROM sales;")
            row = cur.fetchone()
        return jsonify({
            "status": "healthy",
            "service": "RetailPulse API",
            "sales_rows": row["cnt"],
        })
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


# ── Root ─────────────────────────────────────────────────────────
@app.route("/")
def index():
    return jsonify({
        "name": "RetailPulse API",
        "version": "1.0.0",
        "endpoints": [
            "/api/health",
            "/api/sales/summary",
            "/api/sales/by-region",
            "/api/sales/by-category",
            "/api/sales/timeseries",
            "/api/products/top",
            "/api/regions",
        ]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("FLASK_PORT", 5000)), debug=True)
