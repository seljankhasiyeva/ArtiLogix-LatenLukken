# ArtiLogix 🚛
### AI System for Logistics Cost & Volume Prediction

ArtiLogix is a two-sided logistics intelligence platform built for the Azerbaijani freight market. It combines machine learning demand forecasting with a rule-based transport planning chain and an LLM-powered natural language interface — enabling both marketplace operators and logistics managers to make data-driven dispatch decisions.

---

## 🔍 Problem

Azerbaijan's logistics sector is fragmented and reactive:
- Marketplace operators cannot estimate shipping cost at order placement
- Logistics managers dispatch vehicles without knowing next-week demand
- Dead-weight loss and over-provisioning are common due to lack of forecasting tools

ArtiLogix solves this with a 4-step intelligent chain:

```
Predict Orders → Derive Load → Select Vehicle → Calculate Cost
      ML               ML           Logic            Formula
```

---

## ✨ Features

- **Weekly demand forecasting** per region using LightGBM + Prophet
- **Load (desi) estimation** via chained regression model
- **Rule-based vehicle selection** — 5-tier decision table, cold-chain support, consolidation logic
- **Deterministic cost calculation** from a fixed price table
- **LLM chat interface** (Claude Sonnet) for natural language dispatch queries in Azerbaijani and English
- **Two-portal web app** — Marketplace portal and Logistics manager dashboard
- **Real-time streaming** responses via SSE

---

## 👥 Team

| Role | Responsibilities |
|---|---|
| Seljan Khasiyeva - AI Engineer | Data Pipeline · Backend API · Frontend/UI · Deployment |
| Zarifa Musayeva - ML Engineer | EDA & Research · Logic Layer · LLM Integration |
| Firuddin Rzayev - Data Scientist | ML Step 1 (Order Forecast) · Evaluation · Presentation |
| Jabrail Atakishiyev - Data Scientist | ML Step 2 (Load Derivation) · Evaluation · Presentation |

---

## 📅 Progress Log

| Date | Completed |
|---|---|
| Mon, Jun 29 | D-01: Loaded 15 parquet files into DuckDB (110K orders, 16K shipments) · D-02: weekly_orders_by_region view (3,340 rows, 10 regions) · B-01: FastAPI scaffold, 4 routers, DuckDB service · B-03: JWT authentication, demo users, token endpoint |
| Tue, Jun 30 | D-03: order_shipment_join view (25,877 rows, 0 NULLs) · D-04: 4 analytics views (regional_demand_trend, delay_rate_by_route, vehicle_usage_distribution, top_routes_by_cost) · D-05: Data quality report (Khankendi bug confirmed fixed, outlier flagged in actual_load_ton) · D-06: .gitignore, .env.example, branch structure · B-02: DuckDB query helpers (query, query_df) |
| Wed, Jul 1 | |
| Thu, Jul 2 | |
| Fri, Jul 3 | |
| Mon, Jul 7 | |
| Tue, Jul 8 | |
| Wed, Jul 9 | |
| Thu, Jul 10 | |
| Fri, Jul 11 | |
| Mon, Jul 14 | |
| Tue, Jul 15 | |
| Wed, Jul 16 | |
| Thu, Jul 17 | |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Vanilla JS)            │
│         Marketplace Portal │ Logistics Dashboard    │
└────────────────┬────────────────────┬───────────────┘
                 │                    │
┌────────────────▼────────────────────▼────────────────┐
│              Python FastAPI  (port 8001)             │
│   /predict/forecast  │  /predict/load  │  /chat      │
│   /predict/dispatch  │  /predict/cost  │  /analytics │
└────────────┬─────────────────────────┬───────────────┘
             │                         │
   ┌──────────▼──────────┐   ┌─────────▼────────┐
   │   ML Models         │   │   Claude Sonnet  │
   │  LightGBM (x10)     │   │   Tool Calling   │
   │  Prophet (baseline) │   │   SSE Streaming  │
   │  Ridge Regression   │   └──────────────────┘
   └──────────┬──────────┘
              │
   ┌──────────▼──────────┐
   │       DuckDB        │
   │  15 CSV datasets    │
   │  Analytics views    │
   └─────────────────────┘
```

---

## 📊 Dataset

15 synthetic CSV files calibrated from 4 local logistics professional interviews and benchmarked against AWS/Kaggle logistics datasets.

| Dataset | Rows | Role |
|---|---|---|
| orders.csv | 110,000 | Step 1 ML training — weekly order counts per region |
| tir_shipments.csv | 16,000 | Step 2 ML training — actual load tonnage |
| vehicles.csv | 60 | Step 4 price table — fixed fee + variable cost/km |
| routes_history.csv | 3,000 | Road distances for cost calculation |
| spot_pricing.csv | 2,000 | Market demand index (feature only, not target) |
| deliveries.csv | 50,000 | Last-mile analytics |
| + 9 supporting CSVs | Various | Warehouses, couriers, weather, holidays, GPS, traffic |

**Coverage:** 10 Azerbaijan regions · 2020–2026 · 110,000+ orders

---

## 🤖 ML Pipeline

ArtiLogix answers one question: **"How many vehicles do I need next week, and what will it cost?"**

It does this in four steps — only the first two use machine learning:

---

### Step 1 — How many orders are coming? *(Machine Learning)*

We look at the past 4 weeks of order history for each region and predict how many orders will arrive next week. The model learns patterns like "orders spike before Novruz" or "Absheron always has 3× more volume than Sheki."

- Covers all 10 Azerbaijan regions separately
- Trained on 6 years of data (2020–2024), tested on 2025–2026
- Target accuracy: within 20% of actual order count

---

### Step 2 — How much cargo is that? *(Machine Learning)*

Order count alone does not tell us how heavy the shipment will be. A region that ships electronics weighs more than one that ships textiles. We convert order count into estimated tonnage (desi) using regional averages.

- Formula: `estimated load = predicted orders × average weight per order`
- Average weight varies by region and season

---

### Step 3 — Which vehicle? *(Simple Rules)*

Once we know the load, we pick the right vehicle from a fixed table. No machine learning needed here — the rules are straightforward:

| Load | Vehicle |
|---|---|
| Under 500 desi | Ford Transit (small van) |
| 500 – 1,500 desi | Gazelle or Isuzu (medium truck) |
| 1,500 – 4,000 desi | Mercedes Atego (large truck) |
| Over 4,000 desi | TIR (full semi-trailer) |
| Temperature-sensitive cargo | Refrigerated variant of above |

---

### Step 4 — What does it cost? *(Fixed Formula)*

Cost is calculated directly from a price table — no guessing, no model:

```
total_cost_azn = (fixed_fee × days) + (distance_km × variable_cost_per_km) + toll_fees
```

Every rate comes from a fixed price table maintained by the logistics team.
The system tells you exactly which row of that table applies — that is the value machine learning provides.

---

## 🧠 LLM Interface

Instead of navigating dashboards and filling forms, you can simply ask ArtiLogix a question — in Azerbaijani or English — and it will run the full 4-step chain behind the scenes and give you a plain-language answer.

**Examples of what you can ask:**

> *"How many orders are expected in Ganja next week?"*
> *"What vehicle should I send to Lankaran on Friday?"*
> *"What if demand in Sheki is 20% higher than forecast?"*
> *"Show me the cost history for the Baku to Ganja route."*

ArtiLogix understands what you are asking, calls the right calculations automatically, and responds with a complete dispatch recommendation — forecast, load estimate, vehicle choice, and cost — all in one message.

---

**Two modes depending on who is asking:**

- **Marketplace view** — focused on individual orders: estimated cost, delivery time, vehicle type for your shipment.
- **Logistics manager view** — focused on weekly planning: how many vehicles to prepare per region, total cost projections, route efficiency.

---

*Powered by Claude Sonnet (Anthropic) with tool calling — the AI never guesses numbers, it always runs the actual calculation before responding.*

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| ML Models | LightGBM · Prophet · Ridge Regression · scikit-learn |
| Model Serving | Python FastAPI · Joblib |
| Database | DuckDB (file-based, columnar) |
| LLM | Claude Sonnet (Anthropic API) · Tool Calling · SSE |
| Frontend | Vanilla HTML / CSS / JavaScript · Chart.js 4 |
| Deployment | Docker Compose · nginx reverse proxy |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Anthropic API key

### Installation

```bash
git clone https://github.com/seljankhasiyeva/ArtiLogix-LatenLukken.git
cd ArtiLogix-LatenLukken
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
```

### Run with Docker

```bash
docker compose up --build
```

Open `http://localhost:80` — Marketplace portal loads by default.

### Run locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

---

## 📁 Project Structure

```
artilogix/
├── data/
│   ├── raw/                  # 15 synthetic CSV files
│   └── duckdb/               # artilogix.duckdb
├── ml/
│   ├── models/               # .joblib files (LightGBM, Prophet, Ridge)
│   ├── forecast.py           # Step 1 — order volume forecast
│   ├── load_pipeline.py      # Step 2 — desi derivation
│   ├── vehicle_selector.py   # Step 3 — decision table
│   └── cost_calculator.py    # Step 4 — deterministic cost
├── api/
│   ├── main.py               # FastAPI app
│   ├── routers/              # forecast, dispatch, chat, analytics
│   └── llm_service.py        # Claude API + tool calling
├── frontend/
│   ├── marketplace/          # Marketplace portal
│   └── logistics/            # Logistics dashboard
├── tests/
│   └── test_logic.py         # 20 unit tests (Step 3+4)
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 📈 Success Metrics

| Metric | Target |
|---|---|
| Order forecast MAPE | ≤ 20% per region |
| Load derivation R² | ≥ 0.70 |
| Vehicle selection coverage | 100% (no unhandled case) |
| Cost calculation error | 0% (deterministic) |
| LLM tool call precision | ≥ 90% (45/50 queries) |
| LLM hallucination rate | < 5% |
| API latency p50 | < 2.5 seconds |



---

## ⚠️ Limitations

- All data is **synthetically generated** — real-world performance may differ
- Pricing rates are market estimates, not official tariff documents
- Single DuckDB file — no replication or HA

---

## 📄 License

This project was developed as an academic capstone project. June 2026.
