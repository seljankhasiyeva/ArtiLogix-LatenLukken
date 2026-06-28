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
| orders.csv | 50,000 | Step 1 ML training — weekly order counts per region |
| tir_shipments.csv | 8,000 | Step 2 ML training — actual load tonnage |
| vehicles.csv | 60 | Step 4 price table — fixed fee + variable cost/km |
| routes_history.csv | 2,000 | Road distances for cost calculation |
| spot_pricing.csv | 2,000 | Market demand index (feature only, not target) |
| deliveries.csv | 50,000 | Last-mile analytics |
| + 9 supporting CSVs | Various | Warehouses, couriers, weather, holidays, GPS, traffic |

**Coverage:** 10 Azerbaijan regions · 2020–2026 · 50,000+ orders

---

## 🤖 ML Pipeline

### Step 1 — Order Volume Forecast (Core ML)
- **Model:** LightGBM (primary) + Prophet (baseline)
- **Target:** `weekly_order_count` per region
- **Features:** `lag_1w`, `lag_2w`, `lag_4w`, `rolling_mean_4w`, `month`, `week_of_year`, `is_holiday`, `days_to_holiday`
- **Split:** 2020–2024 train / 2025–2026 test
- **Target metric:** MAPE ≤ 20% per region

### Step 2 — Load Derivation (Secondary ML)
- **Model:** Ridge Regression
- **Formula:** `desi_estimate = forecast_orders × avg_weight_model.predict(region, month)`
- **Target metric:** R² ≥ 0.70 (chained)

### Step 3 — Vehicle Selection (Rule-Based)

| Desi Range | Vehicle |
|---|---|
| < 500 | Ford Transit 2t |
| 500 – 1,500 | Gazelle 3t / Isuzu NPR 5t |
| 1,500 – 4,000 | Mercedes Atego 10t |
| > 4,000 | TIR 20t |
| Any + cold_chain | Refrigerated variant |

### Step 4 — Cost Calculation (Deterministic)

```
total_cost_azn = (fixed_fee × days) + (distance_km × variable_cost_per_km) + toll_fees
```

---

## 🧠 LLM Interface

ArtiLogix uses **Claude Sonnet** via the Anthropic API with tool calling to orchestrate the full 4-step chain:

| Tool | Trigger |
|---|---|
| `get_weekly_forecast(region, date_from)` | "How many orders expected in Ganja next week?" |
| `get_dispatch_plan(region, date)` | "What vehicle should I send to Lankaran?" |
| `get_scenario(region, delta_pct)` | "What if demand is 20% higher in Sheki?" |
| `get_route_history(origin, dest)` | "Show me Baku→Ganja cost history" |

Two role-based system prompts: **Marketplace** (order-level) and **Logistics** (dispatch planning).

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
git clone https://github.com/your-org/artilogix.git
cd artilogix
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

## 👥 Team

| Role | Responsibilities |
|---|---|
| AI Engineer | Data Pipeline · Backend API · Frontend/UI · Deployment |
| ML Engineer | EDA & Research · Logic Layer · LLM Integration |
| Data Scientist 1 | ML Step 1 (Order Forecast) · Evaluation · Presentation |
| Data Scientist 2 | ML Step 2 (Load Derivation) · Evaluation · Presentation |

---

## ⚠️ Limitations

- All data is **synthetically generated** — real-world performance may differ
- Pricing rates are market estimates, not official tariff documents
- Demo credentials are hard-coded — not production-ready
- Single DuckDB file — no replication or HA

---

## 📄 License

This project was developed as an academic capstone project. June 2026.
