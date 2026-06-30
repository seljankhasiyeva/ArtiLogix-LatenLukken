# Target 1 — Order Volume Forecast

## Overview

Target 1 is the core machine learning task of the AstroLogix logistics forecasting system. Its objective is to predict **how many orders will arrive per region over the next 7 days**, using historical order data combined with weather conditions and public holiday information.

The output of Target 1 feeds directly into Target 2 (load/desi estimation) and Target 3 (vehicle selection and cost calculation). Without an accurate order volume forecast, the downstream decisions about fleet capacity and routing costs cannot be made reliably. This is why Target 1 is treated as the foundation of the entire pipeline.

---

## Problem Statement

Given historical daily order counts per region, forecast the number of orders for each of the 9 active regions across a 7-day horizon.

- **Unit of prediction:** orders per region per day
- **Forecast horizon:** 7 days
- **Granularity:** region-day (one row = one region, one date)
- **Regions:** Absheron, Ganja, Khachmaz, Lankaran, Nakhchivan, Qazakh, Sheki, Yevlakh, one additional region derived from data

---

## Data Sources

Three parquet files are used as inputs.

### orders.parquet
The primary source. Each row is one customer order.

| Column | Type | Description |
|---|---|---|
| `order_id` | string | Unique order identifier |
| `region` | string | Origin region of the order |
| `item_count` | int | Number of items in the order |
| `created_at` | datetime | Timestamp when the order was placed |
| `delivery_type` | string | Standard or express delivery |
| `shipment_id` | string | Foreign key to TIR shipment (or UNASSIGNED) |

Orders are aggregated to the region-day level to produce the target variable `order_count`.

### weather.parquet
Daily weather observations per region.

| Column | Type | Description |
|---|---|---|
| `timestamp` | datetime (tz-aware) | Observation time (UTC, stripped during load) |
| `region` | string | Region of observation |
| `temperature` | float | Temperature in Celsius |
| `rainfall` | float | Daily rainfall in mm |
| `wind_speed` | float | Wind speed in km/h |

Weather is averaged per region per day and merged onto the daily order table. Missing values are filled using the median for that region and month combination.

### holidays.parquet
Public and national holiday dates.

| Column | Type | Description |
|---|---|---|
| `date` | datetime | Holiday date |
| `event_name` | string | Name of the holiday |
| `region` | string | Region scope (or national) |

Holidays are used to construct three features: a binary flag for the holiday itself, a flag for the day before, and a flag for the day after, plus a continuous feature measuring the distance in days to the nearest holiday.

---

## Pipeline Structure

```
orders.parquet
weather.parquet      →   Daily aggregation   →   Feature engineering   →   Train/test split
holidays.parquet

                                                                             ↓
                                                                     6 ML models trained
                                                                             ↓
                                                                     Model comparison
                                                                             ↓
                                                                    Best model selected
                                                                             ↓
                                                               Recursive 7-day forecast
                                                                             ↓
                                                              Per-region forecast table
                                                                    + heatmap output
```

---

## Feature Engineering

The daily table has one row per (region, date) pair. A total of 46 features are constructed across six categories.

### Time Features (14 features)

These capture the cyclical and structural patterns in order volume.

| Feature | Description |
|---|---|
| `dayofweek` | 0 = Monday, 6 = Sunday |
| `month` | 1–12 |
| `quarter` | 1–4 |
| `year` | Calendar year |
| `dayofyear` | 1–366 |
| `week` | ISO week number |
| `is_weekend` | 1 if Saturday or Sunday |
| `is_month_end` | 1 if last day of the month |
| `is_holiday` | 1 if a public holiday |
| `trend` | Days elapsed since the start of the dataset (captures long-term growth) |
| `sin_dow` | Sine encoding of day of week (circular, avoids 0–6 ordinal bias) |
| `cos_dow` | Cosine encoding of day of week |
| `sin_month` | Sine encoding of month |
| `cos_month` | Cosine encoding of month |

Sine and cosine encodings are used for cyclic features (day of week, month) so the model understands that Sunday (6) and Monday (0) are adjacent, not distant.

### Lag Features (10 features)

Lag features capture the autoregressive structure of the time series. Each lag is computed per region independently using groupby shift.

| Feature | Description |
|---|---|
| `lag_1` | Orders yesterday |
| `lag_2` | Orders 2 days ago |
| `lag_3` | Orders 3 days ago |
| `lag_7` | Orders exactly one week ago |
| `lag_14` | Orders two weeks ago |
| `lag_21` | Orders three weeks ago |
| `lag_28` | Orders four weeks ago |
| `lag_364` | Orders on same weekday last year minus 1 day |
| `lag_365` | Orders on same calendar date last year |
| `lag_366` | Orders on same calendar date last year plus 1 day |

The prior-year lags (364, 365, 366) are included because order volume has strong annual seasonality. Taking three adjacent days around the one-year mark accounts for leap year shifts and ensures the model sees the correct day-of-week alignment.

### Rolling Features (9 features)

Rolling statistics are computed over a lagged window (shifted by 1) to avoid leakage.

| Feature | Description |
|---|---|
| `rolling_mean_3` | 3-day trailing average (excluding today) |
| `rolling_mean_7` | 7-day trailing average |
| `rolling_mean_14` | 14-day trailing average |
| `rolling_mean_28` | 28-day trailing average |
| `rolling_std_3` | 3-day trailing standard deviation |
| `rolling_std_7` | 7-day trailing standard deviation |
| `rolling_std_14` | 14-day trailing standard deviation |
| `rolling_std_28` | 28-day trailing standard deviation |
| `rolling_mean_365` | 365-day trailing average (requires at least 30 data points) |

Standard deviation features give the model a signal about how volatile recent demand has been, which helps calibrate uncertainty around forecasts.

### Holiday Proximity Features (3 features)

Beyond the binary holiday flag, these features help the model learn pre-holiday spikes and post-holiday rebounds.

| Feature | Description |
|---|---|
| `days_to_holiday` | Days to the nearest holiday in either direction (integer, 0 on the day itself) |
| `is_holiday_eve` | 1 if tomorrow is a public holiday |
| `is_holiday_after` | 1 if yesterday was a public holiday |

### Weather Features (3 features)

| Feature | Description |
|---|---|
| `temperature` | Daily average temperature for the region |
| `rainfall` | Daily total rainfall for the region |
| `wind_speed` | Daily average wind speed for the region |

Weather affects consumer behavior — heavy rainfall in particular tends to suppress delivery orders in some regions and increase them in others.

### Order Behavior Features (3 features)

| Feature | Description |
|---|---|
| `avg_item_count` | Average items per order on that day for that region |
| `express_ratio` | Fraction of orders placed as express delivery |
| `region_enc` | Integer encoding of the region name (LabelEncoder, fit on all regions) |

---

## Target Variable

```
order_count = number of orders placed on a given day in a given region
```

The target is computed by counting distinct `order_id` values per (date, region) group.

---

## Train / Test Split

A strict time-based split is used. No random shuffling is ever applied to a time series, as it would cause future data to appear in the training set.

- **Training set:** all data before 2026-04-13
- **Test set:** all data from 2026-04-13 onward (~60 days)
- **Rationale:** the test window is long enough to contain multiple weekly cycles and at least one holiday period, giving a realistic estimate of deployment performance

Missing rows caused by lag features requiring more history than is available (especially the 366-day lags) are dropped with `dropna()` before splitting.

---

## Models

Six models are trained and compared. All models use GridSearchCV with 10-fold cross-validation scored on R².

### Model 1 — Random Forest Regressor

An ensemble of decision trees trained with bagging. Robust to outliers and non-linear relationships. Hyperparameters were fixed to best-found values from prior search.

Key parameters:
- `n_estimators = 253`
- `max_depth = 7`
- `min_samples_leaf = 10`
- `max_features = 0.78`
- `bootstrap`: searched over [True, False]

GridSearchCV fits: 20 (2 combinations × 10 folds)

### Model 2 — XGBoost Regressor

Gradient boosted trees with regularization. Strong on tabular data with mixed feature types. Uses L2 regularization (`reg_lambda = 8.0`) to prevent overfitting on the dense lag feature set.

Key parameters:
- `n_estimators = 100`
- `learning_rate = 0.24`
- `max_depth = 3`
- `reg_lambda = 8.0`
- `colsample_bytree = 0.8`

GridSearchCV fits: 10 (1 combination × 10 folds, single candidate)

### Model 3 — LightGBM Regressor

Leaf-wise gradient boosting. Faster than XGBoost on large datasets and typically produces better results on time series tasks with many lag features. Parameters were fixed to best-found values from prior Optuna optimization.

Key parameters:
- `num_leaves = 71`
- `max_depth = 9`
- `learning_rate = 0.0315783`
- `n_estimators = 376`
- `subsample = 0.941667`
- `colsample_bytree = 0.65587`

Cross-validation is run separately with `cross_val_score` (10-fold R²) before final fit.

### Model 4 — CatBoost Regressor

Gradient boosting with symmetric trees and built-in handling for categorical features. Configured with 1500 iterations at a low learning rate for stability.

Key parameters:
- `iterations = 1500`
- `learning_rate = 0.03`
- `depth = 6`
- `l2_leaf_reg = 5`
- `boosting_type = Plain`
- `boost_from_average = True`

Cross-validation is run with `cross_val_score` (10-fold R²) before final fit.

### Model 5 — Gradient Boosting Regressor (sklearn)

The standard sklearn implementation of gradient boosting. Uses Huber loss, which is more robust to outliers than squared error. Parameters were fixed to best-found values from prior search.

Key parameters:
- `loss = huber`
- `n_estimators = 285`
- `learning_rate = 0.123`
- `max_depth = 8`
- `max_leaf_nodes = 30`
- `subsample = 0.952`

GridSearchCV fits: 10 (1 combination × 10 folds)

### Model 6 — Ridge Regression (baseline)

A linear model with L2 regularization. Included as a statistical baseline. Cannot capture non-linear interactions between lag features and time components, so it is expected to underperform the tree-based models. Demonstrates the performance floor a simple linear approach achieves.

Key parameters:
- `alpha`: searched over 50 values linearly spaced between 1.0 and 100.0

GridSearchCV fits: 500 (50 combinations × 10 folds)

---

## Evaluation Metrics

Each model is evaluated on both training and test sets using four metrics.

| Metric | Formula | Interpretation |
|---|---|---|
| MAE | mean(|actual - predicted|) | Average absolute error in order units. Primary ranking metric. |
| RMSE | sqrt(mean((actual - predicted)²)) | Penalizes large errors more than MAE. Sensitive to outliers. |
| R² | 1 - SS_res / SS_tot | Proportion of variance explained. 1.0 is perfect; below 0.7 is poor for this task. |
| MAPE | mean(|actual - predicted| / actual) × 100 | Percentage error. Computed only on test set. Undefined when actual = 0, handled with +1e-6 offset. |

The best model is selected by lowest Test MAE.

---

## Model Results

Approximate results from the trained models:

| Model | Train R² | Test R² | Test MAE | Notes |
|---|---|---|---|---|
| LightGBM | 0.927 | 0.840 | best | Best overall |
| CatBoost | 0.915 | 0.839 | close second | Near-identical to LightGBM |
| XGBoost | 0.868 | 0.826 | — | Slightly weaker generalization |
| RandomForest | 0.836 | 0.817 | — | Consistent, less variance |
| GradientBoosting | 0.937 | 0.815 | — | Highest overfitting gap |
| Ridge | 0.741 | 0.734 | worst | Cannot model non-linearity |

The overfitting gap in GradientBoosting (Train R² 0.937 vs Test R² 0.815) is the largest among tree models, suggesting it has memorized local patterns in the training period that do not generalize. LightGBM and CatBoost show the best balance between fit quality and generalization.

---

## 7-Day Recursive Forecast

### Why recursive forecasting

A standard forecast computes all 7 days simultaneously using only historical data. A recursive forecast computes day 1, then appends that prediction to the history, then computes day 2 using the updated history, and so on. This matters because lag features like `lag_1` and `lag_2` for day 7 of the forecast refer to day 6 and day 5 — days that do not exist in the historical record. Without recursion, these values would default to the last known real observation, which is incorrect and causes all 7 days to be predicted as if from the same baseline.

### How it works

For each region:

1. Build a working series from the region's full history in `daily_clean`.
2. For each of the 7 future dates:
   - Construct the full feature row using the working series for all lag and rolling lookups.
   - Look up weather using the historical monthly average for that region and month.
   - Look up holiday features using the precomputed `hol_sorted` list.
   - Predict using the best trained model.
   - Append the prediction to the working series so that the next iteration can use it as a lag.
3. Return the 7 daily predictions.

### Safe value lookup

A dedicated `get_value(series, date)` function handles lookups safely:
- If the date exists in the series index, return its value.
- If the series is empty, return 0.0.
- Otherwise fall back to the last known value (`series.iloc[-1]`).

This prevents the `IndexError` that occurs when `iloc[-1]` is called on an empty Series.

### Output format

Results are assembled into a pivot table with regions as rows and dates as columns, plus a TOTAL (7 days) column summing across the week. Regions are sorted descending by total forecast volume.

---

## Visualizations

### Model comparison panel (2×3 grid)

- Test MAE bar chart — ranked lowest to highest
- Test R² bar chart — ranked highest to lowest
- MAPE bar chart — ranked lowest to highest
- Actual vs Predicted scatter (best model, first 300 test samples)
- Absheron region time series — actual vs best model forecast over the test period
- Top 15 feature importances (horizontal bar chart, best model only)

### 7-day forecast panel (1×2)

- Heatmap of forecast orders (regions × dates), color-coded by intensity
- Total 7-day orders by region (bar chart, descending)

---

## Model Persistence

All six trained models are saved to disk using joblib for use in downstream notebooks (Target 2, Target 3).

| File | Model |
|---|---|
| `best_random_forest_model.joblib` | Random Forest |
| `best_xgboost_model.joblib` | XGBoost |
| `best_lightgbm.joblib` | LightGBM |
| `catboost_model.joblib` | CatBoost |
| `model_gradient_boosting-best.joblib` | Gradient Boosting |
| `model_ridge-best.joblib` | Ridge |

The best model (by Test MAE) is used for the 7-day recursive forecast. All six models remain available if a different downstream task prefers a different model.

---

## Position in the Full Pipeline

Target 1 is the first step in a three-stage chain:

```
Target 1: predict order count per region per day
    ↓
Target 2: predict load (desi) = order count × average weight distribution
    ↓
Target 3: select vehicle type based on forecasted load → calculate cost from price table
```

Only Targets 1 and 2 involve machine learning. Target 3 is deterministic logic applied to the outputs of the first two stages.

---

## Key Design Decisions

**Time-based split over random split.** Shuffling rows would allow future order counts to appear in training, making any metric on the test set meaningless. The cutoff date approach mirrors what happens in production: the model always trains on the past and predicts the future.

**Lag-based features over ARIMA-style differencing.** Tree-based models do not assume stationarity and cannot directly model autocorrelation the way ARIMA does. Instead, lag and rolling features make the autocorrelation structure explicit as input columns, which gradient boosted trees and random forests can exploit effectively.

**Prior-year lags (364, 365, 366).** Annual seasonality (New Year orders, Novruz, Ramadan) is one of the strongest signals in the data. Lags at 365 ± 1 days are included to handle leap year shifts and ensure the model sees the correct prior-year day of week.

**Recursive forecast over direct multi-step.** A direct multi-step approach would train a separate model for each horizon (h=1, h=2, ..., h=7). The recursive approach reuses one model and feeds predictions back as inputs. Recursive forecasts accumulate error across steps but are simpler to maintain and require only one model per region. For a 7-day horizon, the error accumulation is acceptable.

**Ridge as baseline.** Including Ridge serves two purposes: it establishes a performance floor (what a linear model achieves), and it makes the value of non-linear models quantifiable. If Ridge were within 5% of LightGBM on Test R², the complexity of gradient boosting would be harder to justify.
