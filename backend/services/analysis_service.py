"""
Pandas-based data analysis service.
All calculations are done with pandas — the LLM only explains results.
"""

import os
import pandas as pd

from utils.data_profile import generate_profile
from utils.rag import add_chunks


# ─────────────────────────────────────────────
# CSV Loading
# ─────────────────────────────────────────────

def load_csv(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV not found: {filepath}")

    # lightweight loading
    return pd.read_csv(filepath)


# ─────────────────────────────────────────────
# Column Detection
# ─────────────────────────────────────────────

def detect_columns(df):
    columns = df.columns.tolist()

    col_lower = [c.lower().strip() for c in columns]

    detected = {
        'sales_col': None,
        'region_col': None,
        'department_col': None,
        'month_col': None
    }

    # Sales column
    for i, cl in enumerate(col_lower):
        if any(k in cl for k in ['sales', 'revenue', 'amount', 'total']):
            if pd.api.types.is_numeric_dtype(df.iloc[:, i]):
                detected['sales_col'] = columns[i]
                break

    # fallback numeric column
    if detected['sales_col'] is None:
        numeric_cols = df.select_dtypes(include='number').columns

        if len(numeric_cols):
            detected['sales_col'] = numeric_cols[0]

    # Region column
    for i, cl in enumerate(col_lower):
        if any(k in cl for k in ['region', 'area', 'zone', 'territory']):
            detected['region_col'] = columns[i]
            break

    # Department column
    for i, cl in enumerate(col_lower):
        if any(k in cl for k in ['department', 'dept', 'team', 'division']):
            detected['department_col'] = columns[i]
            break

    # Month/date column
    for i, cl in enumerate(col_lower):
        if any(k in cl for k in ['month', 'date', 'period', 'time']):
            detected['month_col'] = columns[i]
            break

    return detected


# ─────────────────────────────────────────────
# KPI Generation
# ─────────────────────────────────────────────

def generate_kpis(df, detected, region_grouped=None, dept_grouped=None):

    kpis = {
        'total_records': len(df),
        'total_sales': None,
        'avg_sale': None,
        'top_region': None,
        'top_region_sales': None,
        'top_department': None,
        'top_department_sales': None
    }

    sales_col = detected.get('sales_col')

    if sales_col and sales_col in df.columns:

        kpis['total_sales'] = round(
            float(df[sales_col].sum()),
            2
        )

        kpis['avg_sale'] = round(
            float(df[sales_col].mean()),
            2
        )

    # Top region (from pre-grouped if available)
    if region_grouped is not None:
        if len(region_grouped):
            kpis['top_region'] = str(region_grouped.index[0])
            kpis['top_region_sales'] = round(float(region_grouped.iloc[0]), 2)
    else:
        region_col = detected.get('region_col')
        if region_col and sales_col:
            grouped = (
                df.groupby(region_col)[sales_col]
                .sum()
                .sort_values(ascending=False)
            )
            if len(grouped):
                kpis['top_region'] = str(grouped.index[0])
                kpis['top_region_sales'] = round(float(grouped.iloc[0]), 2)

    # Top department (from pre-grouped if available)
    if dept_grouped is not None:
        if len(dept_grouped):
            kpis['top_department'] = str(dept_grouped.index[0])
            kpis['top_department_sales'] = round(float(dept_grouped.iloc[0]), 2)
    else:
        department_col = detected.get('department_col')
        if department_col and sales_col:
            grouped = (
                df.groupby(department_col)[sales_col]
                .sum()
                .sort_values(ascending=False)
            )
            if len(grouped):
                kpis['top_department'] = str(grouped.index[0])
                kpis['top_department_sales'] = round(float(grouped.iloc[0]), 2)

    return kpis


# ─────────────────────────────────────────────
# Group Formatting
# ─────────────────────────────────────────────

def _group_and_format(df, group_col, val_col, label):

    grouped = (
        df.groupby(group_col)[val_col]
        .agg(
            total_sales='sum',
            count='count',
            avg_sale='mean'
        )
        .reset_index()
    )

    grouped.columns = [
        label,
        'total_sales',
        'count',
        'avg_sale'
    ]

    grouped = grouped.sort_values(
        'total_sales',
        ascending=False
    )

    results = []

    for _, row in grouped.iterrows():

        results.append({
            label: str(row[label]),
            'total_sales': round(float(row['total_sales']), 2),
            'count': int(row['count']),
            'avg_sale': round(float(row['avg_sale']), 2),
        })

    return results


# ─────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────

def get_sales_by_region(df, detected):

    rc = detected.get('region_col')
    sc = detected.get('sales_col')

    if not rc or not sc:
        return []

    return _group_and_format(
        df,
        rc,
        sc,
        'region'
    )


def get_sales_by_department(df, detected):

    dc = detected.get('department_col')
    sc = detected.get('sales_col')

    if not dc or not sc:
        return []

    return _group_and_format(
        df,
        dc,
        sc,
        'department'
    )


def get_monthly_trends(df, detected):

    mc = detected.get('month_col')
    sc = detected.get('sales_col')

    if not mc or not sc:
        return []

    result = _group_and_format(
        df,
        mc,
        sc,
        'month'
    )

    return result


# ─────────────────────────────────────────────
# Summary Statistics
# ─────────────────────────────────────────────

def get_summary_statistics(df):

    numeric_cols = (
        df.select_dtypes(include='number')
        .columns
        .tolist()
    )

    categorical_cols = (
        df.select_dtypes(include='object')
        .columns
        .tolist()
    )

    stats = {}

    for col in numeric_cols:

        stats[col] = {
            'mean': round(float(df[col].mean()), 2),
            'median': round(float(df[col].median()), 2),
            'min': round(float(df[col].min()), 2),
            'max': round(float(df[col].max()), 2),
            'std': round(float(df[col].std()), 2),
            'nulls': int(df[col].isnull().sum()),
            'total': round(float(df[col].sum()), 2),
        }

    return {
        'rows': len(df),
        'columns': len(df.columns),
        'column_names': df.columns.tolist(),
        'numeric_columns': numeric_cols,
        'categorical_columns': categorical_cols,

        # TinyLlama optimization
        'head': df.head(10).to_dict(orient='records'),

        'stats': stats,
    }


# ─────────────────────────────────────────────
# Main Pipeline
# ─────────────────────────────────────────────

def run_full_analysis(filepath):

    if isinstance(filepath, list):
        filepath = filepath[0]

    df = load_csv(filepath)

    # LIMIT HUGE DATASETS
    if len(df) > 1000:
        df = df.head(1000)

    detected = detect_columns(df)

    # PRE-COMPUTE GROUPED DATA to avoid redundant groupby (Fix F)
    rc = detected.get('region_col')
    dc = detected.get('department_col')
    sc = detected.get('sales_col')

    region_grouped = None
    dept_grouped = None
    if rc and sc:
        region_grouped = df.groupby(rc)[sc].sum().sort_values(ascending=False)
    if dc and sc:
        dept_grouped = df.groupby(dc)[sc].sum().sort_values(ascending=False)

    # Data profiling
    profile = generate_profile(df)

    # Lightweight RAG chunks
    chunks = (
        df.astype(str)
        .apply(
            lambda row: " | ".join(row),
            axis=1
        )
        .tolist()
    )

    # IMPORTANT:
    # limit chunk count for low RAM laptops
    add_chunks(filepath)

    return {
        'summary': get_summary_statistics(df),

        'profile': profile,

        'kpis': generate_kpis(
            df,
            detected,
            region_grouped=region_grouped,
            dept_grouped=dept_grouped,
        ),

        'sales_by_region': get_sales_by_region(
            df,
            detected
        ),

        'sales_by_department': get_sales_by_department(
            df,
            detected
        ),

        'monthly_trends': get_monthly_trends(
            df,
            detected
        ),

        'detected_columns': detected,

        '_df': df,
    }


# ─────────────────────────────────────────────
# QA Pandas Helpers (vectorized, 10k+ capable)
# ─────────────────────────────────────────────

def qa_sum(df, column):
    s = df[column]
    return {
        "column": column,
        "value": round(float(s.sum()), 2),
        "operation": "sum",
    }


def qa_average(df, column):
    s = df[column]
    return {
        "column": column,
        "value": round(float(s.mean()), 2),
        "operation": "average",
    }


def qa_count(df):
    return {
        "rows": len(df),
        "operation": "count",
    }


def qa_max(df, column):
    s = df[column]
    return {
        "column": column,
        "value": round(float(s.max()), 2),
        "operation": "max",
    }


def qa_min(df, column):
    s = df[column]
    return {
        "column": column,
        "value": round(float(s.min()), 2),
        "operation": "min",
    }


def qa_trend(df, date_col, value_col):
    if pd.api.types.is_datetime64_any_dtype(df[date_col]):
        dti = df[date_col]
    else:
        dti = pd.to_datetime(df[date_col], errors="coerce")
    trend = df[value_col].groupby(dti.dt.to_period("M")).sum().dropna()
    data = [(str(k), round(float(v), 2)) for k, v in trend.items()]
    direction = "stable"
    if len(data) >= 2:
        direction = "increasing" if data[-1][1] > data[0][1] else "decreasing"
    return {
        "column": value_col,
        "direction": direction,
        "period": "monthly",
        "data": data,
        "operation": "trend",
    }


# ─────────────────────────────────────────────
# Mapping Helpers (auto-detect numeric cols)
# ─────────────────────────────────────────────

def _numeric_cols(df):
    return df.select_dtypes(include="number").columns.tolist()


def map_sum(df):
    cols = _numeric_cols(df)
    return {c: round(float(df[c].sum()), 2) for c in cols}


def map_average(df):
    cols = _numeric_cols(df)
    return {c: round(float(df[c].mean()), 2) for c in cols}


def map_count(df):
    return {"rows": len(df)}


def map_max(df):
    cols = _numeric_cols(df)
    return {c: round(float(df[c].max()), 2) for c in cols}


def map_min(df):
    cols = _numeric_cols(df)
    return {c: round(float(df[c].min()), 2) for c in cols}


# ─────────────────────────────────────────────
# Lightweight Trend Analysis (auto-detect)
# ─────────────────────────────────────────────

def _detect_date_col(df):
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return col
    for col in df.columns:
        cl = col.lower()
        if any(kw in cl for kw in ["date", "time", "month", "year", "period"]):
            return col
    return None


def detect_trends(df):
    date_col = _detect_date_col(df)
    numeric_cols = _numeric_cols(df)
    if not date_col or not numeric_cols:
        return {"trends": [], "direction": "unknown"}
    dti = df[date_col]
    if not pd.api.types.is_datetime64_any_dtype(dti):
        dti = pd.to_datetime(dti, errors="coerce")
    results = []
    overall_directions = set()
    for col in numeric_cols:
        trend = df[col].groupby(dti.dt.to_period("M")).sum().dropna()
        if len(trend) < 2:
            continue
        vals = trend.values
        direction = "increasing" if vals[-1] > vals[0] else "decreasing"
        overall_directions.add(direction)
        results.append({
            "column": col,
            "direction": direction,
            "change": round(float(vals[-1] - vals[0]), 2),
            "first": round(float(vals[0]), 2),
            "last": round(float(vals[-1]), 2),
        })
    return {
        "trends": results,
        "direction": "mixed" if len(overall_directions) > 1 else (overall_directions.pop() if overall_directions else "stable"),
    }