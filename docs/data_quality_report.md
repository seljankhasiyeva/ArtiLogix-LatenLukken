# Data Quality Report
**ArtiLogix — D-05 Task**
**Date:** 2026-06-13
**Dataset version:** v3 (110K orders)

---

## Row Counts

| Table | Rows | Note |
|---|---|---|
| couriers | 200 | — |
| deliveries | 50,000 | Same as v2 |
| gps_logs | 100,000 | 2x v2 |
| holidays | 135 | — |
| inventory | 6,000 | 2x v2 |
| orders | 110,000 | 2x v2 (was 50K) |
| routes_history | 3,000 | 2x v2 |
| spot_pricing | 2,000 | Same as v2 |
| stores | 150 | — |
| tir_shipments | 16,000 | 2x v2 (was 8K) |
| traffic | 30,000 | 2x v2 |
| transfer_center | 5,000 | — |
| vehicles | 60 | — |
| warehouse | 32 | 2x v2 |
| weather | 23,570 | New in v3 |

---

## UNASSIGNED Orders

- Total: 110,000
- Assigned to shipment: 54,405 (49.5%)
- UNASSIGNED: 55,595 (50.5%)

**Note:** UNASSIGNED orders represent real demand not yet packed into a TIR.
These are included in Step 1 time-series training but excluded from Step 2 join.

---

## NULL Check

All critical columns: **0 NULLs** ✓

---

## Region Check

All 10 regions present ✓
Khankendi bug from v2 is fixed ✓

---

## Date Range

- Min: 2020-01-01
- Max: 2026-06-12

---

## Outliers

`actual_load_ton` Max: 21.711t — exceeds TIR capacity (20t).
Possible generator artifact. **DS-2 must handle this in Step 2 training.**

## Data Type Issues

`created_at` stored as VARCHAR in all tables.
All views and queries must use `CAST(created_at AS TIMESTAMP)`.
DS-1 and DS-2 must apply the same cast in their notebooks.

---

## Summary

Dataset v3 is clean and ready for ML pipeline.
One outlier flagged (actual_load_ton > 20t) — monitor in Step 2.