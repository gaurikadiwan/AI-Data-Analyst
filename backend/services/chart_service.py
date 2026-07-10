"""
Chart Service
Uses matplotlib to create visualizations from pandas analysis results.
All charts are saved to the backend/charts/ directory.
This is a refactored version of the original chart_generator.py.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import uuid
from datetime import datetime


CHART_STYLE = {
    'figure_size': (10, 6),
    'dpi': 100,
    'title_fontsize': 14,
    'label_fontsize': 12,
    'colors': ['#2196F3', '#4CAF50', '#FF9800', '#E91E63', '#9C27B0', '#00BCD4'],
}


def _get_chart_dir():
    """Get the charts directory path."""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'charts')


def _save_chart(fig, prefix):
    """
    Save a matplotlib figure to the charts directory.
    Returns the relative URL path to the saved chart.
    """
    chart_dir = _get_chart_dir()
    os.makedirs(chart_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{prefix}_{timestamp}_{unique_id}.png"
    filepath = os.path.join(chart_dir, filename)

    fig.savefig(filepath, dpi=CHART_STYLE['dpi'], bbox_inches='tight')
    plt.close(fig)

    return f"/charts/{filename}"


def generate_bar_chart(data, x_key, y_key, title, x_label, y_label, prefix="bar"):
    """Generate a bar chart and save it. Returns URL path to the saved chart image."""
    if not data:
        return None

    fig, ax = plt.subplots(figsize=CHART_STYLE['figure_size'])
    labels = [str(d[x_key]) for d in data]
    values = [d[y_key] for d in data]
    bars = ax.bar(labels, values, color=CHART_STYLE['colors'][:len(labels)])

    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + max(values) * 0.01,
            f'{val:,.0f}', ha='center', va='bottom', fontsize=10,
        )

    ax.set_title(title, fontsize=CHART_STYLE['title_fontsize'], fontweight='bold', pad=15)
    ax.set_xlabel(x_label, fontsize=CHART_STYLE['label_fontsize'])
    ax.set_ylabel(y_label, fontsize=CHART_STYLE['label_fontsize'])
    ax.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    return _save_chart(fig, prefix)


def generate_line_chart(data, x_key, y_key, title, x_label, y_label, prefix="line"):
    """Generate a line chart and save it. Returns URL path to the saved chart image."""
    if not data:
        return None

    fig, ax = plt.subplots(figsize=CHART_STYLE['figure_size'])
    labels = [str(d[x_key]) for d in data]
    values = [d[y_key] for d in data]

    ax.plot(labels, values, marker='o', linewidth=2.5, markersize=8,
            color=CHART_STYLE['colors'][0], markerfacecolor='white',
            markeredgewidth=2, markeredgecolor=CHART_STYLE['colors'][0])

    ax.fill_between(range(len(labels)), values, alpha=0.1, color=CHART_STYLE['colors'][0])

    for i, val in enumerate(values):
        ax.text(i, val + max(values) * 0.02, f'{val:,.0f}',
                ha='center', va='bottom', fontsize=10)

    ax.set_title(title, fontsize=CHART_STYLE['title_fontsize'], fontweight='bold', pad=15)
    ax.set_xlabel(x_label, fontsize=CHART_STYLE['label_fontsize'])
    ax.set_ylabel(y_label, fontsize=CHART_STYLE['label_fontsize'])
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return _save_chart(fig, prefix)


def generate_pie_chart(data, label_key, value_key, title, prefix="pie"):
    """Generate a pie chart and save it. Returns URL path to the saved chart image."""
    if not data:
        return None

    fig, ax = plt.subplots(figsize=CHART_STYLE['figure_size'])
    labels = [str(d[label_key]) for d in data]
    values = [d[value_key] for d in data]
    colors = CHART_STYLE['colors'][:len(labels)]

    wedges, texts, autotexts = ax.pie(
        values, labels=labels, autopct='%1.1f%%',
        colors=colors, startangle=90, textprops={'fontsize': 11},
    )
    for autotext in autotexts:
        autotext.set_fontweight('bold')

    ax.set_title(title, fontsize=CHART_STYLE['title_fontsize'], fontweight='bold', pad=15)
    plt.tight_layout()
    return _save_chart(fig, prefix)


def generate_all_charts(analysis_result):
    """
    Generate all three standard charts from analysis results.
    Returns dict with chart URLs: {sales_by_region, monthly_trend, department_sales}.
    """
    charts = {}

    region_data = analysis_result.get('sales_by_region', [])
    if region_data:
        charts['sales_by_region'] = generate_bar_chart(
            data=region_data, x_key='region', y_key='total_sales',
            title='Sales by Region', x_label='Region', y_label='Total Sales',
            prefix='region_bar',
        )

    trend_data = analysis_result.get('monthly_trends', [])
    if trend_data:
        charts['monthly_trend'] = generate_line_chart(
            data=trend_data, x_key='month', y_key='total_sales',
            title='Monthly Sales Trend', x_label='Month', y_label='Total Sales',
            prefix='monthly_line',
        )

    dept_data = analysis_result.get('sales_by_department', [])
    if dept_data:
        charts['department_sales'] = generate_pie_chart(
            data=dept_data, label_key='department', value_key='total_sales',
            title='Department-wise Sales Distribution', prefix='dept_pie',
        )

    return charts
