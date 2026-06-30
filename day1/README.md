# Day 1 — Monday (Week 1)

## DS-1 — M1-01: LightGBM Model Initialization

**Task:** Initial setup of the LightGBM model for Target 1 (order count forecast).
**Status:** Started (to be continued on Day 4)
**To-Do List:**

* Check the existing feature engineering pipeline in `target_1.ipynb` (lag, rolling, calendar features).
* Fit a baseline LightGBM model using initial (default) parameters.
* Prepare the train/validation split (to be strictly finalized on Day 3).

**Reference Files:** `target_1.ipynb` (LightGBM section), `target_1_documentation.md`

## DS-2 — M2-01: Ridge Regression Model (avg_weight) — Initiation

**Task:** Start building the Ridge Regression model to predict the average weight per order (`avg_weight`) as a sub-model for Target 2.
**To-Do List:**

* Prepare the `avg_weight` target variable from `orders.parquet` and `tir_shipments.parquet` (based on `actual_load_ton / num_packages`, see `target_3_documentation.md` §"Unit Conversion").
* Prepare the feature matrix for Ridge (region, date, seasonality).
* Run an initial trial fit using `Ridge(alpha=1.0)`.

**Reference Files:** `target_2.ipynb` (introductory sections), `model_ridge.joblib` (initial, untuned)

---

### Expected Outputs at the End of the Day

* [ ] LightGBM baseline code (committed)
* [ ] Ridge initial model code (committed)
* [ ] `model_ridge.joblib` (untuned version)