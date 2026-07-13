"""
Simple prompts for AI Data Analyst.
Optimized for TinyLlama.
"""

from utils.prompt_builder import build_mode_prompt


# ============================================================
# Insight Prompt
# ============================================================

def build_insight_prompt(summary, mode=None):

    base = build_mode_prompt(
        summary,
        mode=mode
    )

    return f"""<sys>KPI analyst</sys>
{base}
{summary}
Key findings? Trends? Action?
Base on numbers. Be concise."""


# ============================================================
# QA Prompt
# ============================================================

def build_qa_prompt(
    schema,
    summary,
    relevant_rows,
    question,
    profile=None,
    mode=None,
    conversation_history=None
):

    schema_text = (
        ",".join(schema)
        if isinstance(schema, list)
        else str(schema)
    )

    rows_text = "\n".join(
        str(r)
        for r in relevant_rows[:3]
    ) if relevant_rows else ""

    history_text = ""
    if conversation_history:
        pairs = []
        for q, a in conversation_history[-2:]:
            pairs.append(f"Q:{q} A:{a}")
        history_text = "|".join(pairs) + " "

    column_list = "\n".join(f"  - {col}" for col in (schema if isinstance(schema, list) else []))

    return f"""DATASET COLUMNS (only use these exact names):
{column_list}

AVAILABLE DATA:
{summary}
{rows_text}
{history_text}

RULE: Only reference columns from the list above. Do not invent or assume column names.

Q: {question}
A:"""


# ============================================================
# Recommendation Prompt
# ============================================================

def build_recommendation_prompt(
    summary,
    profile,
    mode=None
):

    nulls = profile.get(
        "missing_values",
        {}
    )

    missing = {
        k: v
        for k, v in nulls.items()
        if v > 0
    }

    quality_note = ""
    if missing:
        items = ",".join(f"{k}({v})" for k, v in missing.items())
        quality_note = f" miss={{{items}}}"

    return f"""<sys>advisor</sys>
{summary}{quality_note}
Opportunity? Risk? Recommendation? Steps."""


# ============================================================
# Profile Prompt
# ============================================================

def build_profile_prompt(profile_summary):

    return f"""<sys>data QC</sys>
{profile_summary}
Quality? Biggest issue? Next step?"""