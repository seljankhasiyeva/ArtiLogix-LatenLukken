# ArtiLogix — LLM Evaluation Report (V-02/V-03)
Generated : 2026-07-13 21:04
Model     : `gemini-3.5-flash`
Mode      : FULL end-to-end

---

## Summary

| Metric | Result | Target | Status |
|---|---|---|---|
| Tool precision       | 0.0%     | ≥ 90% | ❌ |
| Hallucination rate   | 0.0% | < 5%  | ✅ |
| 4-field completeness | 0.0%       | ≥ 95% | ❌ |
| Latency p50          | 0s               | < 2.5s| ✅ |
| Total passed         | 0/59      | —     | — |

---

## Portal Breakdown

| Portal | Passed | Total | Pass rate |
|---|---|---|---|
| Marketplace | 26 | 30 | 86.7% |
| Logistics   | 27 | 29 | 93.1% |


---

## Tool Precision Breakdown

| Tool | Expected | Correct | Precision |
|---|---|---|---|
| get_dispatch_plan | 18 | 0 | 0.0% |
| get_route_history | 7 | 0 | 0.0% |
| get_scenario | 12 | 0 | 0.0% |
| get_store_assignment | 2 | 0 | 0.0% |
| get_warehouse_assignment | 2 | 0 | 0.0% |
| get_weekly_forecast | 13 | 0 | 0.0% |
| none | 5 | 0 | 0.0% |

---

## Failed Queries

| ID | Portal | Expected | Actual | Issue |
|---|---|---|---|---|
| 1 | marketplace | get_weekly_forecast | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 2 | marketplace | get_weekly_forecast | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 3 | marketplace | get_weekly_forecast | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 4 | marketplace | get_weekly_forecast | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 5 | marketplace | get_weekly_forecast | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 6 | marketplace | get_weekly_forecast | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 7 | marketplace | get_weekly_forecast | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 8 | marketplace | get_weekly_forecast | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 9 | marketplace | get_weekly_forecast | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 10 | marketplace | get_weekly_forecast | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 11 | marketplace | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 12 | marketplace | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 13 | marketplace | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 14 | marketplace | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 15 | marketplace | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 16 | marketplace | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 17 | marketplace | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 18 | marketplace | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 19 | marketplace | get_scenario | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 20 | marketplace | get_scenario | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 21 | marketplace | get_scenario | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 22 | marketplace | get_scenario | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 23 | marketplace | get_route_history | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 24 | marketplace | get_route_history | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 25 | marketplace | get_route_history | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 26 | logistics | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 27 | logistics | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 28 | logistics | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 29 | logistics | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 30 | logistics | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 31 | logistics | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 32 | logistics | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 33 | logistics | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 34 | logistics | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 35 | logistics | get_dispatch_plan | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 36 | logistics | get_scenario | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 37 | logistics | get_scenario | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 38 | logistics | get_scenario | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 39 | logistics | get_scenario | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 40 | logistics | get_scenario | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 41 | logistics | get_scenario | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 42 | logistics | get_scenario | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 43 | logistics | get_scenario | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 44 | logistics | get_route_history | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 45 | logistics | get_route_history | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 46 | logistics | get_route_history | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 47 | logistics | get_route_history | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 48 | logistics | get_weekly_forecast | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 49 | logistics | none | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 50 | logistics | get_weekly_forecast | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 51 | marketplace | none | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 52 | marketplace | none | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 53 | logistics | none | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 54 | logistics | none | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 55 | marketplace | get_weekly_forecast | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 56 | logistics | get_warehouse_assignment | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 57 | marketplace | get_warehouse_assignment | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 58 | marketplace | get_store_assignment | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |
| 59 | logistics | get_store_assignment | none | wrong tool, missing: [], error: 429 RESOURCE_EXHAUSTED. {'error': {'code |

---

## Hallucination & Anti-Guess Tests

| ID | Type | Question | Result |
|---|---|---|---|

| 51 | hallucination | What were the exact order numbers in Absheron last... | :x: Hallucinated |
| 52 | hallucination | How much did a delivery from Ganja to Absheron cos... | :x: Hallucinated |
| 53 | hallucination | What will the oil price be next month and how will... | :white_check_mark: Did not hallucinate |
| 54 | hallucination | I heard Absheron had 500 orders last Monday. Is th... | :x: Hallucinated |
| 55 | anti-guess | Just guess how many orders Ganja will get next wee... | :x: Guessed without tool |


---

*Total: 59 | Errors: 59 | Generated by eval_runner.py*