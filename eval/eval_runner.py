import sys
import json
import time
import requests
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

load_dotenv()

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
QUERIES_FILE = "eval/eval_queries.json"
REPORT_FILE  = "eval/llm_eval_report.md"

# ── MOCK MODE ─────────────────────────────────────────────────────────────────
# True  → FastAPI çağırışı yoxdur, yalnız Gemini tool seçimi yoxlanılır
# False → FastAPI işləyir, tam end-to-end test
MOCK_FASTAPI = False

from google import genai
from google.genai import types
from app.llm.tools import TOOL_ENDPOINT_MAP, POST_TOOLS, build_gemini_tools

client = genai.Client()

MARKETPLACE_PROMPT = Path("app/llm/system_prompts/marketplace.txt").read_text(encoding="utf-8")
LOGISTICS_PROMPT   = Path("app/llm/system_prompts/logistics.txt").read_text(encoding="utf-8")


def _system_prompt(portal: str) -> str:
    return MARKETPLACE_PROMPT if portal == "marketplace" else LOGISTICS_PROMPT


def _first_function_call_part(response) -> types.Part | None:
    if not response.candidates or not response.candidates[0].content:
        return None
    for part in response.candidates[0].content.parts or []:
        if part.function_call is not None:
            return part
    return None


def _call_gemini(portal: str, question: str) -> tuple[types.GenerateContentResponse, float]:
    system_prompt = _system_prompt(portal)
    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=build_gemini_tools(),
        temperature=0.1,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    max_retries = 5
    backoff = 2
    for attempt in range(max_retries):
        try:
            t0 = time.time()
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=question,
                config=config,
            )
            latency = round(time.time() - t0, 2)
            return response, latency
        except Exception as e:
            err_str = str(e)
            is_transient = any(
                term in err_str.upper()
                for term in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "OVERLOADED"]
            )
            if is_transient:
                if attempt < max_retries - 1:
                    sleep_time = backoff ** attempt + 2
                    print(f"         [API ERROR] Got transient error, sleeping {sleep_time}s before retry (attempt {attempt+1}/{max_retries})... Error: {err_str[:60]}")
                    time.sleep(sleep_time)
                    continue
            raise e


def _call_fastapi(tool_name: str, arguments: dict) -> dict:
    if MOCK_FASTAPI:
        return {"mock": True, "tool": tool_name}
    endpoint = TOOL_ENDPOINT_MAP.get(tool_name)
    if not endpoint:
        return {"error": f"No endpoint for {tool_name}"}
    try:
        if tool_name in POST_TOOLS:
            r = requests.post(f"http://localhost:8001{endpoint}", params=arguments, timeout=10)
        else:
            r = requests.get(f"http://localhost:8001{endpoint}", params=arguments, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def _extract_tool_call(response: types.GenerateContentResponse) -> str | None:
    fc_part = _first_function_call_part(response)
    if fc_part:
        return fc_part.function_call.name
    return None


def _extract_tool_call_args(response: types.GenerateContentResponse) -> dict:
    fc_part = _first_function_call_part(response)
    if fc_part:
        fc = fc_part.function_call
        return dict(fc.args) if fc.args else {}
    return {}


def _extract_answer_text(response: types.GenerateContentResponse) -> str:
    fc_part = _first_function_call_part(response)
    if fc_part:
        return ""
    return response.text or ""


def _check_fields(answer_text: str, expected_fields: list[str]) -> dict:
    if not expected_fields:
        return {"all_present": True, "missing": []}
    missing = [f for f in expected_fields if f not in answer_text]
    return {"all_present": len(missing) == 0, "missing": missing}


def _check_hallucination(query: dict, tool_called: str | None, answer_text: str) -> bool:
    if query.get("should_hallucinate") is not True:
        return False
    behavior = query.get("expected_behavior", "")
    if behavior in ("refuse_or_clarify", "refuse_or_redirect"):
        return bool(tool_called) or any(c.isdigit() for c in answer_text)
    return False


def _check_anti_guess(query: dict, tool_called: str | None) -> bool | None:
    if not query.get("anti_guess_test"):
        return None
    return tool_called == query.get("expected_tool")


def evaluate_query(query: dict) -> dict:
    question     = query["question"]
    portal       = query["portal"]
    exp_tool     = query.get("expected_tool")
    exp_fields   = query.get("expected_fields", [])
    exp_behavior = query.get("expected_behavior")

    try:
        response, latency = _call_gemini(portal, question)
    except Exception as e:
        return {
            "id": query["id"], "portal": portal, "question": question,
            "expected_tool": exp_tool, "actual_tool": None,
            "tool_correct": False, "fields_ok": False, "missing_fields": [],
            "hallucinated": False, "anti_guess_ok": None,
            "latency_s": None, "error": str(e), "pass": False,
        }

    actual_tool  = _extract_tool_call(response)
    answer_text  = _extract_answer_text(response)

    if actual_tool:
        if MOCK_FASTAPI:
            # Mock mode: don't hit FastAPI, just fake an answer that
            # contains all expected fields so the field check passes.
            _call_fastapi(actual_tool, {})
            answer_text = " ".join(exp_fields)
        else:
            # Full mode: actually call FastAPI with the real arguments
            # the model produced, and check the tool's real JSON result
            # for the expected field names (the LLM's natural-language
            # reply won't contain literal snake_case keys like
            # "forecast_orders", so we check the data, not the prose).
            tool_args   = _extract_tool_call_args(response)
            tool_result = _call_fastapi(actual_tool, tool_args)
            answer_text = json.dumps(tool_result, ensure_ascii=False)

    field_result = _check_fields(answer_text, exp_fields)
    hallucinated = _check_hallucination(query, actual_tool, answer_text)
    anti_guess   = _check_anti_guess(query, actual_tool)

    if exp_tool is None and exp_behavior in (
        "ask_clarification", "refuse_or_clarify", "refuse_or_redirect"
    ):
        tool_correct = actual_tool is None
    else:
        tool_correct = actual_tool == exp_tool

    passed = (
        tool_correct
        and field_result["all_present"]
        and not hallucinated
        and (anti_guess is None or anti_guess)
    )

    return {
        "id": query["id"], "portal": portal, "question": question,
        "expected_tool": exp_tool, "actual_tool": actual_tool,
        "tool_correct": tool_correct, "fields_ok": field_result["all_present"],
        "missing_fields": field_result["missing"], "hallucinated": hallucinated,
        "anti_guess_ok": anti_guess, "latency_s": latency,
        "error": None, "pass": passed,
    }


def run_eval(queries_file: str = QUERIES_FILE) -> list[dict]:
    with open(queries_file, encoding="utf-8") as f:
        data = json.load(f)

    queries = data["queries"]
    results = []

    mode = "MOCK (tool selection only)" if MOCK_FASTAPI else "FULL (end-to-end)"
    print(f"Running {len(queries)} queries | model={GEMINI_MODEL} | mode={mode}")
    print()

    for i, query in enumerate(queries, 1):
        print(f"  [{i:2d}/{len(queries)}] id={query['id']:2d} | {query['question'][:55]}...")
        result = evaluate_query(query)
        status = "PASS" if result["pass"] else "FAIL"
        err_str = f" | ERR: {result['error'][:60]}" if result["error"] else ""
        print(f"         -> {status} | tool={result['actual_tool']} | latency={result['latency_s']}s{err_str}")
        results.append(result)
        time.sleep(4.5)

    return results


def _generate_report(results: list[dict]) -> str:
    total        = len(results)
    passed       = sum(1 for r in results if r["pass"])
    tool_correct = sum(1 for r in results if r["tool_correct"])
    hallucinated = sum(1 for r in results if r["hallucinated"])
    errors       = sum(1 for r in results if r["error"])
    latencies    = [r["latency_s"] for r in results if r["latency_s"] is not None]
    p50          = sorted(latencies)[len(latencies) // 2] if latencies else 0

    tool_precision     = round(tool_correct / total * 100, 1)
    hallucination_rate = round(hallucinated / total * 100, 1)
    completeness       = round(sum(1 for r in results if r["fields_ok"]) / total * 100, 1)

    mp  = [r for r in results if r["portal"] == "marketplace"]
    log = [r for r in results if r["portal"] == "logistics"]

    def pct(n, d): return round(n / d * 100, 1) if d else 0

    lines = [
        "# ArtiLogix — LLM Evaluation Report (V-02/V-03)",
        f"Generated : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Model     : `{GEMINI_MODEL}`",
        f"Mode      : {'MOCK — tool selection only' if MOCK_FASTAPI else 'FULL end-to-end'}",
        "",
        "---", "",
        "## Summary", "",
        "| Metric | Result | Target | Status |",
        "|---|---|---|---|",
        f"| Tool precision       | {tool_precision}%     | ≥ 90% | {'✅' if tool_precision >= 90 else '❌'} |",
        f"| Hallucination rate   | {hallucination_rate}% | < 5%  | {'✅' if hallucination_rate < 5 else '❌'} |",
        f"| 4-field completeness | {completeness}%       | ≥ 95% | {'✅' if completeness >= 95 else '❌'} |",
        f"| Latency p50          | {p50}s               | < 2.5s| {'✅' if p50 < 2.5 else '❌'} |",
        f"| Total passed         | {passed}/{total}      | —     | — |",
        "",
        "---", "",
        "## Portal Breakdown", "",
        "| Portal | Passed | Total | Pass rate |",
        "|---|---|---|---|",
        f"| Marketplace | {sum(1 for r in mp if r['pass'])} | {len(mp)} | {pct(sum(1 for r in mp if r['pass']), len(mp))}% |",
        f"| Logistics   | {sum(1 for r in log if r['pass'])} | {len(log)} | {pct(sum(1 for r in log if r['pass']), len(log))}% |",
        "",
        "---", "",
        "## Tool Precision Breakdown", "",
        "| Tool | Expected | Correct | Precision |",
        "|---|---|---|---|",
    ]

    from collections import Counter
    exp_counts  = Counter(r["expected_tool"] or "none" for r in results)
    hit_counts  = Counter(
        r["expected_tool"] or "none"
        for r in results if r["tool_correct"]
    )
    for tool, n in sorted(exp_counts.items()):
        h    = hit_counts.get(tool, 0)
        prec = round(h / n * 100, 1)
        lines.append(f"| {tool} | {n} | {h} | {prec}% |")

    lines += ["", "---", "", "## Failed Queries", ""]
    failed = [r for r in results if not r["pass"]]
    if not failed:
        lines.append("No failed queries. ✅")
    else:
        lines += ["| ID | Portal | Expected | Actual | Issue |", "|---|---|---|---|---|"]
        for r in failed:
            issues = []
            if not r["tool_correct"]:  issues.append("wrong tool")
            if not r["fields_ok"]:     issues.append(f"missing: {r['missing_fields']}")
            if r["hallucinated"]:      issues.append("hallucinated")
            if r["error"]:             issues.append(f"error: {r['error'][:40]}")
            lines.append(
                f"| {r['id']} | {r['portal']} | "
                f"{r['expected_tool'] or 'none'} | "
                f"{r['actual_tool'] or 'none'} | "
                f"{', '.join(issues)} |"
            )

    lines += ["", "---", "", "## Hallucination & Anti-Guess Tests", "",
              "| ID | Type | Question | Result |",
              "|---|---|---|---|"]
    for r in results:
        if r["id"] in {51, 52, 53, 54}:
            status = "✅ Did not hallucinate" if not r["hallucinated"] else "❌ Hallucinated"
            lines.append(f"| {r['id']} | hallucination | {r['question'][:50]}... | {status} |")
        if r["id"] == 55:
            ok = r.get("anti_guess_ok")
            status = "✅ Called tool" if ok else "❌ Guessed without tool"
            lines.append(f"| 55 | anti-guess | {r['question'][:50]}... | {status} |")

    lines += ["", "---", "",
              f"*Total: {total} | Errors: {errors} | Generated by eval_runner.py*"]

    return "\n".join(lines)


def main():
    results = run_eval()
    report  = _generate_report(results)

    Path(REPORT_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report)

    results_path = REPORT_FILE.replace(".md", "_results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 55)
    total    = len(results)
    passed   = sum(1 for r in results if r["pass"])
    tc       = sum(1 for r in results if r["tool_correct"])
    print(f"Tool precision : {round(tc/total*100,1)}%")
    print(f"Passed         : {passed}/{total}")
    print(f"Report         : {REPORT_FILE}")
    print("=" * 55)


if __name__ == "__main__":
    main()