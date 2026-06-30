# Day 2 — Tuesday (Week 1)

## DS-1 — M1-02: Building the Prophet Baseline Model

**Task:** Build a Prophet baseline model (either individual regional models or a global seasonal model) for parallel comparison with LightGBM.
**To-Do List:**

* Convert the `daily` (region × date) data into Prophet format (`ds` and `y` columns).
* Fit a separate Prophet model for each region (`yearly_seasonality=True`, `weekly_seasonality=True`).
* Pass the holiday list (`holidays.parquet`) into Prophet using the `holidays` parameter.
* Save the results to `prophet_baseline_predictions.csv` (this will be required for V-01 on Day 11).

**Why Prophet?** It serves as an industry-standard, simple, and interpretable seasonal baseline—acting as an anchor to measure the incremental accuracy gained by LightGBM.

## DS-2 — M2-01: Finalizing the avg_weight Regression Model

**Task:** Complete the Ridge model initiated yesterday.
**To-Do List:**

* Hyperparameter tuning: Run a small grid search for `alpha` (`[0.1, 1, 10, 50,100]`) using `TimeSeriesSplit`.
* Fit the final model on the entire training dataset and save it as `model_ridge-best.joblib`.
* Calculate Train/Test MAE, RMSE, and $R^2$.

**Reference File:** `model_ridge-best.joblib`

---

### Expected Outputs at the End of the Day

* [ ] Prophet baseline code + `prophet_baseline_predictions.csv`
* [ ] `model_ridge-best.joblib` (M2-01 COMPLETED)