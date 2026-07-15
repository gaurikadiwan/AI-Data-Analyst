"""
AI Service:
Strict data-first architecture. LLM only interprets pre-computed pandas output.
No calculations, no code generation, no column name assumptions.
"""

import re
import json
import time
import logging


from services.analysis_service import run_full_analysis

from services.llm_service import get_llm, get_model_info
from services.chart_service import generate_all_charts


logger = logging.getLogger("api")

# Simple in-memory cache: (input_json, question) -> LLM response text
_RESPONSE_CACHE: dict[tuple[str, str], str] = {}

# Cache: filepath -> run_full_analysis result
_ANALYSIS_CACHE: dict[str, dict] = {}

# ============================================================
# STRICT PROMPT CONSTANTS — shared by tinyllama AND phi3:mini
# ============================================================

OUTPUT_FORMAT = """Respond in JSON only:
{
  "insights": "key observations from the data",
  "recommendations": ["action 1", "action 2"],
  "summary": "one-line executive summary"
}"""


def _trimmed_kpis(kpis):
    result = {}
    for k in ("total_sales", "avg_sale", "total_records"):
        if k in kpis and kpis[k] is not None:
            result[k] = kpis[k]
    if kpis.get("top_region"):
        val = kpis["top_region"]
        if kpis.get("top_region_sales") is not None:
            val = f"{val} ({kpis['top_region_sales']})"
        result["top_region"] = val
    if kpis.get("top_department"):
        val = kpis["top_department"]
        if kpis.get("top_department_sales") is not None:
            val = f"{val} ({kpis['top_department_sales']})"
        result["top_department"] = val
    return result


def _trim_grouped(data, max_rows=5):
    return data[:max_rows] if isinstance(data, list) else data


def _build_strict_input(analysis):
    data = {
        "kpis": _trimmed_kpis(analysis.get("kpis", {})),
        "grouped_metrics": {
            "sales_by_region": _trim_grouped(analysis.get("sales_by_region", [])),
            "sales_by_department": _trim_grouped(analysis.get("sales_by_department", [])),
            "monthly_trends": _trim_grouped(analysis.get("monthly_trends", []))
        }
    }
    return json.dumps(data, indent=2, default=str)


def _build_qa_input(analysis, question):
    data = {
        "kpis": _trimmed_kpis(analysis.get("kpis", {})),
        "grouped_metrics": {
            "sales_by_region": _trim_grouped(analysis.get("sales_by_region", [])),
            "sales_by_department": _trim_grouped(analysis.get("sales_by_department", [])),
            "monthly_trends": _trim_grouped(analysis.get("monthly_trends", []))
        },
        "question": question
    }
    return json.dumps(data, indent=2, default=str)


def _is_safe(text):
    if re.search(r'```(?:python)?\s*\n', text, re.IGNORECASE):
        return False
    if re.search(r'\b(pd\.|pandas|df\[|df\.|plt\.|matplotlib)', text):
        return False
    return True


# ============================================================
# LLM CALL WITH RETRY + SAFETY GUARD
# ============================================================

def _llm_call_with_retry(llm, prompt):
    fallback = json.dumps({
        "insights": "The model failed to generate insights.",
        "recommendations": ["Review the provided KPIs and grouped metrics manually."],
        "summary": "Unable to generate insights from model."
    })
    for attempt in range(2):
        try:
            response = llm.invoke(prompt)
            text = response.content if hasattr(response, "content") else str(response)
            safe = _is_safe(text)
            if not safe:
                if attempt == 1:
                    logger.warning("Unsafe LLM response after retry, using fallback")
                    return {"success": True, "text": fallback}
                logger.warning("Unsafe LLM response, retrying")
                continue
            return {"success": True, "text": text}
        except Exception as e:
            if attempt == 1:
                logger.error(f"LLM call failed after retry: {str(e)}")
                return {"success": True, "text": fallback}
            logger.warning(f"LLM call failed, retrying: {str(e)}")
    return {"success": True, "text": fallback}


# ============================================================
# Pipeline Status
# ============================================================

PIPELINE_STATUS = {
    "upload": "pending",
    "profiling": "pending",
    "insights": "pending",
    "charts": "pending",
    "recommendations": "pending",
    "completed": False,
    "error": None
}


def reset_pipeline_status():
    PIPELINE_STATUS.update({
        "upload": "pending",
        "profiling": "pending",
        "insights": "pending",
        "charts": "pending",
        "recommendations": "pending",
        "completed": False,
        "error": None
    })


# ============================================================
# SAFE RESPONSE WRAPPER (IMPORTANT FIX)
# ============================================================

def safe_result(result):
    """
    Ensures API never crashes on missing keys.
    """
    if not isinstance(result, dict):
        return {
            "success": False,
            "error": "Invalid pipeline response"
        }

    if not result.get("success", True):
        return result

    # ensure keys exist
    result.setdefault("insights", "")
    result.setdefault("recommendation", "")
    result.setdefault("charts", [])
    result.setdefault("profile", {})
    result.setdefault("kpis", {})

    return result


# ============================================================
# DATA QUALITY (FIXED EXPORT ISSUE)
# ============================================================

def run_data_quality(filepath):
    """
    Data quality scoring with severity classification.
    - invalid column usage -> HIGH severity
    - incomplete/truncated data -> CRITICAL severity
    """

    if isinstance(filepath, list):
        filepath = filepath[0]

    if filepath not in _ANALYSIS_CACHE:
        _ANALYSIS_CACHE[filepath] = run_full_analysis(filepath)
    analysis = _ANALYSIS_CACHE[filepath]
    df = analysis.get("_df")
    profile = analysis.get("profile", {})

    nulls = profile.get("missing_values", {})

    total_cells = len(df) * len(df.columns)

    filled_cells = total_cells - sum(nulls.values())

    quality_score = round((filled_cells / max(total_cells, 1)) * 100, 1)

    issues = []

    columns = df.columns.tolist()
    col_lower = [c.strip().lower() for c in columns]
    for i, col in enumerate(columns):
        for j, other in enumerate(columns):
            if i >= j:
                continue
            if col_lower[i] == col_lower[j]:
                issues.append({
                    "severity": "HIGH",
                    "type": "invalid_column_usage",
                    "message": f"Columns '{col}' and '{other}' differ only by case — risk of LLM hallucination",
                    "quality_score_deduction": 15,
                })
        if col != col.strip():
            issues.append({
                "severity": "HIGH",
                "type": "invalid_column_usage",
                "message": f"Column '{col}' has leading/trailing whitespace",
                "quality_score_deduction": 10,
            })

    for col in df.columns:
        str_vals = df[col].astype(str)
        truncated = str_vals.str.contains(r'\.\.\.$', na=False)
        if truncated.any():
            issues.append({
                "severity": "CRITICAL",
                "type": "truncated_data",
                "message": f"Column '{col}' contains truncated values ({int(truncated.sum())} rows)",
                "quality_score_deduction": 25,
            })

    return {
        "quality_score": quality_score,
        "rows": len(df),
        "columns": len(df.columns),
        "missing_values": nulls,
        "duplicate_rows": profile.get("duplicate_rows", 0),
        "issues": issues,
        "quality_breakdown": {
            "completeness": quality_score,
            "has_invalid_columns": len([i for i in issues if i["severity"] == "HIGH"]) > 0,
            "has_truncated_data": len([i for i in issues if i["severity"] == "CRITICAL"]) > 0,
        }
    }


# ============================================================
# INSIGHTS — single LLM call with strict data-only JSON input
# ============================================================

def run_ai_pipeline(filepath, mode=None):

    start = time.time()
    reset_pipeline_status()

    try:

        if isinstance(filepath, list):
            filepath = filepath[0]

        PIPELINE_STATUS["upload"] = "completed"
        PIPELINE_STATUS["profiling"] = "running"

        if filepath not in _ANALYSIS_CACHE:
            _ANALYSIS_CACHE[filepath] = run_full_analysis(filepath)
        analysis = _ANALYSIS_CACHE[filepath]

        PIPELINE_STATUS["profiling"] = "completed"
        PIPELINE_STATUS["charts"] = "running"

        charts = generate_all_charts(analysis)

        analysis["charts"] = charts

        PIPELINE_STATUS["charts"] = "completed"
        PIPELINE_STATUS["insights"] = "running"

        llm = get_llm("phi3:mini")

        strict_input = _build_strict_input(analysis)

        prompt = strict_input + "\n" + OUTPUT_FORMAT

        llm_result = _llm_call_with_retry(llm, prompt)
        text = llm_result.get("text", "")

        PIPELINE_STATUS["insights"] = "completed"
        PIPELINE_STATUS["recommendations"] = "completed"
        PIPELINE_STATUS["completed"] = True

        try:
            parsed = json.loads(text)
            if not isinstance(parsed.get("recommendations"), list):
                parsed["recommendations"] = [str(parsed.get("recommendations", ""))]
        except (json.JSONDecodeError, TypeError):
            parsed = {
                "insights": text,
                "recommendations": [text[:200]],
                "summary": text[:100]
            }

        return {
            "success": True,
            "workflow": PIPELINE_STATUS,
            "insights": parsed.get("insights", text),
            "recommendation": "\n".join(parsed.get("recommendations", [text[:200]])),
            "charts": charts,
            "kpis": analysis.get("kpis", {}),
            "profile": analysis.get("profile", {}),
            "performance": {
                "total_duration": round(time.time() - start, 2),
                "model": get_model_info().get("model"),
            }
        }

    except Exception as e:
        logger.error(f"Pipeline Error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "insights": "",
            "recommendation": "",
            "charts": []
        }


# ============================================================
# FAST MODE — bypass LLM for known factual questions
# ============================================================

def _fast_answer(analysis, question):
    q = question.strip().lower()

    kpis = analysis.get("kpis", {})
    regions = analysis.get("sales_by_region", [])
    departments = analysis.get("sales_by_department", [])
    trends = analysis.get("monthly_trends", [])
    summary = analysis.get("summary", {})

    # summary stats
    if ("summary" in q and "stat" in q) or q in ("overview", "stats"):
        cols = summary.get("columns", 0)
        rows_count = summary.get("rows", 0)
        col_names = summary.get("column_names", [])
        numeric_cols = summary.get("numeric_columns", [])
        stats = summary.get("stats", {})

        lines = [f"**Dataset**: {rows_count} rows x {cols} columns"]
        if col_names:
            lines.append(f"**Columns**: {', '.join(col_names)}")
        if numeric_cols:
            lines.append(f"**Numeric columns**: {', '.join(numeric_cols)}")
        if kpis:
            lines.append("**KPIs**:")
            for k, v in kpis.items():
                if v is not None:
                    lines.append(f"- {k}: {v}")
        if stats:
            lines.append("**Numeric Stats**:")
            for col, s in stats.items():
                lines.append(f"- {col}: mean={s.get('mean','N/A')}, min={s.get('min','N/A')}, max={s.get('max','N/A')}")
        return "\n".join(lines)

    # top regions
    is_region_q = any(w in q for w in ["region", "territory", "area", "zone"])
    is_top_q = any(w in q for w in ["top", "best", "highest", "leading", "rank"])
    if is_region_q and is_top_q:
        top = regions[:5] if regions else []
        if not top:
            return "No region data available."
        lines = ["**Top Regions**"]
        for i, r in enumerate(top, 1):
            lines.append(f"{i}. {r.get('region','?')}: {r.get('total_sales','N/A')} (avg: {r.get('avg_sale','N/A')}, count: {r.get('count','N/A')})")
        return "\n".join(lines)

    # highest sales
    if "highest sales" in q or "top sales" in q or "best sales" in q or "max sale" in q:
        lines = ["**Highest Sales**"]
        if kpis.get("total_sales") is not None:
            lines.append(f"Total sales: {kpis['total_sales']}")
        if kpis.get("avg_sale") is not None:
            lines.append(f"Average sale: {kpis['avg_sale']}")
        if kpis.get("top_region"):
            lines.append(f"Top region: {kpis['top_region']} ({kpis.get('top_region_sales', 'N/A')})")
        if kpis.get("top_department"):
            lines.append(f"Top department: {kpis['top_department']} ({kpis.get('top_department_sales', 'N/A')})")
        if regions:
            lines.append(f"\nHighest region: {regions[0]['region']} ({regions[0]['total_sales']})")
        return "\n".join(lines)

    # distribution / breakdown
    if any(w in q for w in ["distribution", "breakdown", "split", "spread"]):
        lines = ["**Distribution**"]
        if regions:
            lines.append(f"By Region ({len(regions)}):")
            for r in regions:
                lines.append(f"- {r.get('region','?')}: {r.get('total_sales','N/A')}")
        if departments:
            lines.append(f"\nBy Department ({len(departments)}):")
            for d in departments:
                lines.append(f"- {d.get('department','?')}: {d.get('total_sales','N/A')}")
        if trends:
            lines.append(f"\nMonthly Trends ({len(trends)}):")
            for t in trends:
                lines.append(f"- {t.get('month','?')}: {t.get('total_sales','N/A')}")
        return "\n".join(lines)

    # region performance
    if ("region" in q or "territory" in q) and any(w in q for w in ["performance", "sale", "revenue"]):
        if not regions:
            return "No region data available."
        lines = ["**Region Performance**"]
        for r in regions:
            lines.append(f"- {r.get('region','?')}: {r.get('total_sales','N/A')} (avg: {r.get('avg_sale','N/A')}, {r.get('count','N/A')} records)")
        return "\n".join(lines)

    return None


# ============================================================
# QUESTION ANSWERING — strict data-only JSON input
# ============================================================

def answer_question(analysis, question, mode=None):

    fast = _fast_answer(analysis, question)
    if fast is not None:
        logger.info(f"Fast mode answered: {question}")
        return fast

    strict_input = _build_qa_input(analysis, question)
    cache_key = (strict_input, question)

    cached = _RESPONSE_CACHE.get(cache_key)
    if cached is not None:
        logger.info(f"Cache hit for question: {question}")
        return cached

    llm = get_llm()

    def _cache_and_return(val):
        _RESPONSE_CACHE[cache_key] = val
        return val

    try:
        prompt = strict_input + "\n" + OUTPUT_FORMAT

        result = _llm_call_with_retry(llm, prompt)
        text = result.get("text", "")

        try:
            parsed = json.loads(text)
            return _cache_and_return(parsed.get("insights") or parsed.get("summary") or text)
        except (json.JSONDecodeError, TypeError):
            return _cache_and_return(text)

    except Exception as e:
        return _cache_and_return(f"Error: {str(e)}")


# ============================================================
# HEALTH CHECK (NEW - ADD THIS)
# ============================================================

def health_check():
    """
    Backend health status
    """
    try:
        llm = get_llm()
        test = llm.invoke("say ok")

        return {
            "status": "healthy",
            "llm": "ok",
            "model": get_model_info().get("model")
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# ============================================================
# PROFILING AGENT
# ============================================================

class ProfilingAgent:
    def run(self, analysis):
        profile = analysis.get("profile", {})
        return {
            "profile": profile,
            "summary": analysis.get("summary", {}),
            "kpis": analysis.get("kpis", {}),
        }


# ============================================================
# RECOMMENDATION AGENT
# ============================================================

class RecommendationAgent:
    def run(self, analysis, llm, mode=None):
        strict_input = _build_strict_input(analysis)
        prompt = strict_input + "\n" + OUTPUT_FORMAT
        result = _llm_call_with_retry(llm, prompt)
        text = result.get("text", "") if result.get("success") else ""
        try:
            parsed = json.loads(text)
            recs = parsed.get("recommendations", [text])
        except (json.JSONDecodeError, TypeError):
            retry = _llm_call_with_retry(llm, prompt + "\nReturn ONLY valid JSON.")
            retry_text = retry.get("text", "") if retry.get("success") else ""
            try:
                parsed = json.loads(retry_text)
                recs = parsed.get("recommendations", [retry_text])
            except (json.JSONDecodeError, TypeError):
                recs = [text or retry_text]
        return {"text": text, "recommendations": recs}


# ============================================================
# ARCHITECTURE METADATA
# ============================================================

def get_architecture_metadata():
    return {
        "name": "AI Data Analyst",
        "version": "2.0.0",
        "framework": "Flask + LangChain + Ollama",
        "components": {
            "pipeline": "analysis -> profiling -> insights -> charts -> recommendations",
            "models": ["tinyllama", "phi3:mini", "qwen2.5-coder:3b"],
        },
        "services": {
            "ai_service": "loaded",
            "analysis_service": "loaded",
            "llm_service": "loaded",
            "chart_service": "loaded",
            "upload_service": "loaded",
        }
    }


# ============================================================
# MODEL COMPARISON (SAFE)
# ============================================================

def compare_models(question):
    from services.llm_service import get_llm_for_model
    import time

    models = ["tinyllama", "phi3:mini"]
    results = []

    for m in models:
        llm = get_llm_for_model(m)

        start = time.time()
        try:
            res = llm.invoke(question)
            text = res.content if hasattr(res, "content") else str(res)
        except Exception as e:
            text = str(e)

        results.append({
            "model": m,
            "response": text,
            "time": round(time.time() - start, 2)
        })

    return results