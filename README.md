# ArtiLogix
### AI System for Logistics Cost & Volume Prediction

ArtiLogix is a logistics intelligence platform built for the Azerbaijani freight market. It combines machine learning demand forecasting with a rule-based transport planning process and an AI chat assistant — helping both marketplace sellers and logistics managers make delivery decisions based on real data instead of guesswork.

---

## Problem

Azerbaijan's logistics sector is fragmented and reactive:
- Marketplace sellers cannot estimate shipping cost when a customer places an order
- Logistics managers send out vehicles without knowing how much demand is coming next week
- Wasted vehicle space and unnecessary costs are common because there is no forecasting in place

ArtiLogix solves this with a five-model intelligent chain:

```
Predict Orders → Derive Load → Assign Warehouse/Store → Select Vehicle → Calculate Cost
     (AI)            (AI)              (AI)                (Rules)        (Formula)
```

*A sixth model, Warehouse Fill Forecast, runs alongside this chain to flag warehouses approaching full capacity before it becomes a problem. A seventh, Route Delivery Time, has been trained but is not yet connected to a live feature.*

In plain terms: the system predicts how many orders are coming, estimates how heavy that cargo will be, decides which warehouse and store should handle it, picks the right vehicle for the job, and calculates the exact price — automatically, in seconds.

---

## Features

- **Weekly demand forecasting** for each region, using a trained machine learning model
- **Cargo weight estimation**, based on order predictions
- **Automatic vehicle selection** — a clear decision table covering five vehicle sizes, including refrigerated transport and load-combining options
- **Consistent, formula-based pricing** — no guessing, the same rules apply every time
- **AI chat assistant** that understands questions in Azerbaijani or English and replies in English, grounded in actual predictions, not made-up numbers
- **Four separate portals**, one for each type of user: a system administrator, a logistics manager, a marketplace seller, and a delivery driver
- **Live, streaming chat replies** — answers appear word by word, like a real conversation

---

## Team

|
 Role 
|
 Responsibilities 
|
|
---
|
---
|
|
 Seljan Khasiyeva — AI Engineer 
|
 Data Pipeline · Backend API · Frontend/UI · Deployment 
|
|
 Zarifa Musayeva — ML Engineer 
|
 Research & Analysis · Logic Layer · AI Assistant Integration 
|
|
 Firuddin Rzayev — Data Scientist 
|
 Order Forecast Model · Evaluation · Presentation 
|
|
 Jabrail Atakishiyev — Data Scientist 
|
 Cargo Load Model · Evaluation · Presentation 
|

---

## How It Works (In Simple Terms)

ArtiLogix answers one core question: **"How many vehicles do I need next week, and what will it cost?"**

It gets there in six steps, each backed by its own trained model or a simple, predictable rule.

### Step 1 — How many orders are coming? *(Model: Order Forecast)*
The system looks at recent order history for each region and predicts how many orders will arrive next week. It learns real patterns — for example, that some regions consistently get more orders than others, or that certain times of year bring more demand.

### Step 2 — How much cargo is that? *(Model: Cargo Load)*
Knowing the number of orders isn't enough — a heavy shipment and a light one need different vehicles. The system estimates the total weight of the cargo based on the order forecast.

### Step 3 — Which warehouse or store should handle it? *(Models: Warehouse Assignment, Store Assignment)*
For a given order, the system predicts which warehouse should hold the stock and which store should fulfill it — instead of a person having to check manually.

### Step 4 — Which vehicle should we send? *(Rule-based)*
Once the system knows the cargo weight, it picks the right vehicle from a fixed table. This step does not use machine learning — the rules are simple and predictable:

|
 Cargo Load 
|
 Vehicle 
|
|
---
|
---
|
|
 Small 
|
 Van 
|
|
 Medium 
|
 Mid-size truck 
|
|
 Large 
|
 Heavy truck 
|
|
 Very large 
|
 Full trailer (TIR) 
|
|
 Temperature-sensitive cargo 
|
 Refrigerated version of the above 
|

### Step 5 — How long will delivery take? *(Model trained, not yet live)*
A dedicated model for this exists and has been trained on distance, weather, and traffic conditions — but it is not yet connected to a live feature. Right now, this estimate is not part of the active dispatch flow.

### Step 6 — What does it cost? *(Formula-based)*
The final price comes from a fixed pricing formula — distance, vehicle type, and any extra fees. Nothing is guessed; every number can be traced back to a clear rule.

### All Six Trained Models

A seventh model, Warehouse Fill Forecast, runs alongside this chain — not tied to any single order, but continuously watching whether a warehouse is heading toward full capacity in the coming weeks:

|
#
|
 Model 
|
 Predicts 
|
 Status 
|
|
---
|
---
|
---
|
---
|
|
 1 
|
 Order Forecast 
|
 How many orders will arrive next week, per region 
|
 Live — used in Step 1 
|
|
 2 
|
 Cargo Load 
|
 How much weight/volume that translates to 
|
 Live — used in Step 2 
|
|
 3 
|
 Warehouse Assignment 
|
 Which warehouse should fulfill a given order 
|
 Live — used in Step 3 
|
|
 4 
|
 Store Assignment 
|
 Which store should fulfill/receive a given order 
|
 Live — used in Step 3 
|
|
 5 
|
 Route Delivery Time 
|
 How long a delivery will take, based on distance, weather, and traffic 
|
 Trained, not yet connected to a live feature 
|
|
 6 
|
 Warehouse Fill Forecast 
|
 Whether a warehouse will approach full capacity in the coming weeks 
|
 Trained, not yet connected to a live feature 
|

---

## The AI Assistant

Instead of clicking through menus and forms, a user can simply ask ArtiLogix a question — in Azerbaijani or English — and the assistant will run the calculations behind the scenes and reply in plain language. The assistant understands questions in either language but always replies in English.

**Examples of questions you can ask:**

> "How many orders are expected in Ganja next week?"
> "What vehicle should I send to Lankaran on Friday?"
> "What if demand in Sheki is 20 percent higher than expected?"
> "Show me the delivery history for the Baku to Ganja route."

The assistant never makes up numbers. It always runs the real calculation first, then explains the result in a way anyone can understand.

**Two views depending on who is asking:**
- **Marketplace view** — focused on a single order: estimated cost, delivery time, and vehicle type.
- **Logistics manager view** — focused on the bigger picture: how many vehicles to prepare, total costs, and route performance.

*Powered by Google Gemini with tool-calling — the AI assistant calls the real prediction system before it answers, instead of guessing.*

---

## Technology Used (Explained Simply)

|
 Layer 
|
 What it is 
|
 Technology 
|
|
---
|
---
|
---
|
|
 Prediction models 
|
 The "brain" that makes forecasts 
|
 XGBoost and Ridge Regression (machine learning) 
|
|
 Backend 
|
 The engine connecting everything together 
|
 Python, FastAPI 
|
|
 Database 
|
 Where all the data is stored 
|
 DuckDB (a lightweight, file-based database) 
|
|
 AI Assistant 
|
 The chat feature 
|
 Google Gemini, with real-time streaming replies 
|
|
 Website 
|
 What the user sees and clicks on 
|
 Plain HTML, CSS, and JavaScript — no complex framework 
|
|
 Deployment 
|
 How it all runs together 
|
 A single Docker container, serving both the website and the backend from one place 
|

---

## Getting Started

### What you need first
- Python 3.11 or newer
- Docker and Docker Compose
- A Google Gemini API key

### Setup

```bash
git clone https://github.com/seljankhasiyeva/ArtiLogix-LatenLukken.git
cd ArtiLogix-LatenLukken
cp .env.example .env
# Add your GOOGLE_API_KEY to the .env file
```

### Run with Docker (recommended)

```bash
docker compose up --build
```

Then open `http://localhost:8001/login.html` in your browser.

### Run without Docker

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

---

## Project Structure

```
ArtiLogix-LatenLukken/
├── app/
│   ├── logic/              Vehicle selection and cost calculation rules
│   ├── llm/                AI assistant integration and prompt design
│   │   └── system_prompts/ Instructions for the assistant, per user type
│   ├── routers/             All backend API endpoints
│   ├── schemas/             Data validation models
│   ├── services/            Database access and model loading
│   └── static/               The website itself (5 pages, one per user type)
│       ├── css/
│       └── js/
├── data/                    Source data files and the database
├── db/                      One-time setup scripts (build the database)
├── docs/                    Data reports and documentation
├── eval/                    Model and AI assistant evaluation results
│   └── ml_evaluation/
├── models/                  Trained machine learning model files
├── notebooks/               Data analysis and model training notebooks
│   ├── eda/                 Exploratory data analysis
│   └── ml/                  Model training notebooks
├── tests/                   Automated tests
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Target Metrics

These are the goals the system was designed and tested against:

|
 Metric 
|
 Target 
|
|
---
|
---
|
|
 Order forecast accuracy 
|
 Within 20% of actual, per region 
|
|
 Cargo load model fit 
|
 Strong (R² ≥ 0.70) 
|
|
 Vehicle selection coverage 
|
 100% — every case handled, no exceptions 
|
|
 Pricing consistency 
|
 100% — same input always gives the same price 
|
|
 AI assistant tool-use accuracy 
|
 90% or higher 
|
|
 AI assistant made-up answers 
|
 Under 5% of responses 
|

---

## Limitations

- All underlying data is **synthetically generated** for this project — real-world results may differ.
- Pricing figures are estimates, not official published rates.
- The system uses a single database file, with no backup replication.
- Two additional trained models (warehouse capacity forecasting and delivery time prediction) exist but are not yet connected to a live, in-use feature.

---

## License

This project was developed as an academic capstone project, June 2026.
