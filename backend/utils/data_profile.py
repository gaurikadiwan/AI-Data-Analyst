import pandas as pd

def generate_profile(df):
    nulls = df.isnull().sum().to_dict()
    dups = int(df.duplicated().sum())
    total_cells = len(df) * len(df.columns)
    filled = total_cells - sum(nulls.values())
    quality_score = round(filled / max(total_cells, 1) * 100, 1)

    numeric_df = df.select_dtypes(include='number')
    outliers = {}
    for col in numeric_df.columns:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        o = df[(df[col] < lower) | (df[col] > upper)]
        if len(o):
            outliers[col] = int(len(o))

    profile = {
        "rows": len(df),
        "columns": len(df.columns),
        "column_types": df.dtypes.astype(str).to_dict(),
        "missing_values": {k: int(v) for k, v in nulls.items()},
        "missing_pct": {k: round(float(v) / max(len(df), 1) * 100, 1) for k, v in nulls.items() if v > 0},
        "duplicate_rows": dups,
        "quality_score": quality_score,
        "outliers": outliers,
    }

    try:
        profile["summary_statistics"] = (
            df.describe(include="all").fillna("").to_dict()
        )
    except Exception:
        profile["summary_statistics"] = {}

    if not numeric_df.empty:
        try:
            profile["correlations"] = numeric_df.corr().fillna(0).to_dict()
        except Exception:
            profile["correlations"] = {}

    return profile
