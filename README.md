# 🛒 RetailPulse — Dockerized Sales Analytics with Tableau

A production-grade **end-to-end retail analytics pipeline** that ingests raw sales CSV data, loads it into a PostgreSQL database running inside Docker, exposes a REST API for querying, and connects to **Tableau** for live dashboarding.

```
CSV Sales Data → Python ETL → PostgreSQL (Docker) → Flask API → Tableau Dashboard
```

---

## 📐 Architecture

```
┌──────────────────────────────────────────────────────┐
│                  Docker Compose Network              │
│                                                      │
│  ┌─────────────┐    ┌──────────────┐                 │
│  │  PostgreSQL │◄───│  Python ETL  │◄── CSV Files    │
│  │  :5432      │    │  (loader)    │                 │
│  └──────┬──────┘    └──────────────┘                 │
│         │                                            │
│  ┌──────▼──────┐                                     │
│  │  Flask API  │  :5000  ──────────────► Tableau     │
│  │  (REST)     │                        Desktop      │
│  └─────────────┘                                     │
└──────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v24+)
- [Docker Compose](https://docs.docker.com/compose/) (v2+)
- [Tableau Desktop](https://www.tableau.com/products/desktop) (2022.1+) — for dashboard viewing
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/retailpulse.git
cd retailpulse
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your preferred credentials
```

### 3. Start All Services
```bash
make up
# or: docker compose up --build -d
```

### 4. Load Sample Data
```bash
make load-data
# or: docker compose exec etl python loader.py
```

### 5. Verify API
```bash
curl http://localhost:5000/api/health
curl http://localhost:5000/api/sales/summary
```

### 6. Connect Tableau
- Open `tableau/RetailPulse.twb` in Tableau Desktop
- Update the PostgreSQL connection: `localhost:5432`, database `retailpulse`
- Use credentials from your `.env` file

---

## 📁 Project Structure

```
retailpulse/
├── data/                    # Raw CSV sales data
│   ├── sales_2022.csv
│   ├── sales_2023.csv
│   └── sales_2024.csv
├── db/
│   └── init/                # PostgreSQL init SQL scripts
│       ├── 01_schema.sql
│       └── 02_indexes.sql
├── etl/                     # Python ETL pipeline
│   ├── Dockerfile
│   ├── loader.py
│   ├── transformer.py
│   ├── validator.py
│   └── requirements.txt
├── api/                     # Flask REST API
│   ├── Dockerfile
│   ├── app.py
│   ├── routes/
│   │   ├── sales.py
│   │   ├── products.py
│   │   └── regions.py
│   └── requirements.txt
├── tableau/
│   └── RetailPulse.twb      # Tableau workbook (XML)
├── scripts/
│   ├── generate_data.py     # Synthetic data generator
│   └── health_check.sh
├── .github/
│   └── workflows/
│       └── ci.yml           # GitHub Actions CI
├── docs/
│   └── ARCHITECTURE.md
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

---

## 🐳 Docker Services

| Service    | Image              | Port  | Description              |
|------------|--------------------|-------|--------------------------|
| `postgres` | postgres:15-alpine | 5432  | Main database            |
| `etl`      | python:3.11-slim   | —     | Data ingestion pipeline  |
| `api`      | python:3.11-slim   | 5000  | REST API for Tableau     |
| `pgadmin`  | dpage/pgadmin4     | 8080  | DB admin UI (optional)   |

---

## 📊 Tableau Dashboards

The workbook (`tableau/RetailPulse.twb`) includes 4 pre-built sheets:

1. **Sales Overview** — Revenue trend by month/year
2. **Regional Heatmap** — Sales performance by region
3. **Product Mix** — Category breakdown with margin analysis
4. **Executive Dashboard** — KPI summary (combined view)

### Connecting Tableau to Docker PostgreSQL
1. In Tableau Desktop → Connect → PostgreSQL
2. Server: `localhost`, Port: `5432`
3. Database: `retailpulse`
4. Username/Password: from your `.env`

---

## 🔌 API Endpoints

| Method | Endpoint                        | Description               |
|--------|---------------------------------|---------------------------|
| GET    | `/api/health`                   | Service health check      |
| GET    | `/api/sales/summary`            | Aggregated sales summary  |
| GET    | `/api/sales/by-region`          | Sales grouped by region   |
| GET    | `/api/sales/by-category`        | Sales grouped by category |
| GET    | `/api/sales/timeseries`         | Monthly revenue trend     |
| GET    | `/api/products/top`             | Top 10 products by revenue|
| GET    | `/api/products/<id>`            | Single product details    |

---

## 🛠️ Makefile Commands

```bash
make up           # Start all Docker services
make down         # Stop all services
make load-data    # Run ETL to load CSVs into PostgreSQL
make logs         # Tail all container logs
make db-shell     # Open psql shell in postgres container
make test         # Run API tests
make clean        # Remove all containers and volumes
make generate     # Generate fresh synthetic data
```

---

## 🧪 Running Tests

```bash
make test
# or:
docker compose exec api python -m pytest tests/ -v
```

---

## ⚙️ Environment Variables

See `.env.example` for all available options:

```
POSTGRES_DB=retailpulse
POSTGRES_USER=retailuser
POSTGRES_PASSWORD=changeme
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
FLASK_ENV=development
FLASK_PORT=5000
```

---

## 📈 Data Schema

### `sales` table
| Column        | Type      | Description                  |
|---------------|-----------|------------------------------|
| id            | SERIAL PK | Unique sale ID               |
| order_date    | DATE      | Date of order                |
| region        | VARCHAR   | Geographic region            |
| category      | VARCHAR   | Product category             |
| product_name  | VARCHAR   | Product name                 |
| quantity      | INT       | Units sold                   |
| unit_price    | DECIMAL   | Price per unit               |
| discount      | DECIMAL   | Discount applied (0–1)       |
| revenue       | DECIMAL   | Net revenue after discount   |
| profit        | DECIMAL   | Profit after cost            |
| customer_id   | VARCHAR   | Anonymized customer ID       |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'feat: add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with Docker 🐳 + Tableau 📊 + Python 🐍 + PostgreSQL 🐘*
