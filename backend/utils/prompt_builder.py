"""
Lightweight prompt builder.
"""

PROMPT_MODES = {

    "executive_summary": {
        "style": "Clear and business-focused"
    },

    "technical_analysis": {
        "style": "Detailed and analytical"
    },

    "concise": {
        "style": "Short and direct"
    },

    "business_insights": {
        "style": "Strategic and practical"
    },

    "strict_factual": {
        "style": "Only factual observations"
    },
}


def _get_mode(mode):

    mode = mode or "executive_summary"

    if mode not in PROMPT_MODES:
        mode = "executive_summary"

    return PROMPT_MODES[mode]


def build_mode_prompt(
    summary_text,
    mode=None,
    question=None,
    extra_context=None
):

    config = _get_mode(mode)

    lines = [

        f"Style: {config['style']}",

        "",

        summary_text
    ]

    if question:

        lines.extend([

            "",

            f"Question: {question}"
        ])

    if extra_context:

        lines.extend([

            "",

            str(extra_context)
        ])

    return "\n".join(lines)