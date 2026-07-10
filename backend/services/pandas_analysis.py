"""
Lightweight pandas analysis utilities for filtering, summarizing, and retrieving context.
No external vector/embedding dependencies.
"""

import pandas as pd


def filter_rows_by_keywords(df, question, top_k=10):
    question_lower = question.lower()
    keywords = [w for w in question_lower.split() if len(w) > 2]
    if not keywords:
        return df.head(top_k).to_dict(orient='records')

    def score_row(row):
        text = ' '.join(str(v).lower() for v in row.values)
        return sum(1 for kw in keywords if kw in text)

    scored = df.copy()
    scored['_score'] = df.apply(score_row, axis=1)
    scored = scored[scored['_score'] > 0].sort_values('_score', ascending=False)
    if scored.empty:
        return df.head(top_k).to_dict(orient='records')
    return scored.head(top_k).drop(columns=['_score']).to_dict(orient='records')


def get_column_summary(df, col):
    if col not in df.columns:
        return None
    summary = {'name': col, 'dtype': str(df[col].dtype), 'nulls': int(df[col].isnull().sum())}
    if pd.api.types.is_numeric_dtype(df[col]):
        s = df[col].dropna()
        summary.update({
            'min': float(s.min()), 'max': float(s.max()),
            'mean': round(float(s.mean()), 2), 'median': round(float(s.median()), 2),
            'unique': int(s.nunique()),
        })
    else:
        s = df[col].dropna()
        val_counts = s.value_counts().head(5)
        summary.update({
            'unique': int(s.nunique()),
            'top_values': dict(zip(val_counts.index.astype(str).tolist(), val_counts.astype(int).tolist())),
        })
    return summary


def get_compact_summary(df):
    numeric = df.select_dtypes(include='number')
    stats = {}
    for col in numeric.columns:
        s = numeric[col].dropna()
        if len(s):
            stats[col] = {'min': round(float(s.min()), 2), 'max': round(float(s.max()), 2),
                          'mean': round(float(s.mean()), 2)}
    return {
        'rows': len(df),
        'cols': len(df.columns),
        'columns': df.columns.tolist(),
        'numeric_stats': stats,
        'sample': df.head(3).to_dict(orient='records'),
    }
