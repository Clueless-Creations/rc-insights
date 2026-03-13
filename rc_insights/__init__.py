"""rc-insights: Agent-ready RevenueCat Charts API analysis toolkit."""

__version__ = "0.2.0"

from rc_insights.client import ChartsClient, ChartName, ChartResponse, OverviewMetrics, Resolution
from rc_insights.analyzer import InsightsAnalyzer, AnalysisReport, Insight, Severity, InsightCategory, HealthScore
from rc_insights.report import ReportGenerator
from rc_insights.analyzer import ToolResult

__all__ = [
    "ChartsClient", "ChartName", "ChartResponse", "OverviewMetrics", "Resolution",
    "InsightsAnalyzer", "AnalysisReport", "Insight", "Severity", "InsightCategory", "HealthScore",
    "ReportGenerator", "ToolResult", "describe",
]


def describe() -> dict:
    """Self-describing capability manifest for agent discovery.
    
    Returns a structured description of everything rc-insights can do,
    in a format any agent can parse without reading documentation.
    """
    return {
        "name": "rc-insights",
        "version": __version__,
        "description": "RevenueCat Charts API analysis toolkit. Pulls subscription metrics, analyzes trends and anomalies, generates health scores and reports.",
        "discovery": {
            "method": "ChartsClient.list_available_charts()",
            "description": "Dynamically discovers available chart types from the API at runtime."
        },
        "tools": [
            {
                "name": "get_overview",
                "description": "Get current overview metrics (MRR, active subs, trials, revenue, new customers).",
                "inputs": {},
                "output": "OverviewMetrics with .mrr, .active_subscriptions, .active_trials, .revenue, .new_customers",
            },
            {
                "name": "get_chart",
                "description": "Query a specific chart metric over a date range.",
                "inputs": {
                    "chart_name": "One of the chart names from list_available_charts(). Required.",
                    "start_date": "YYYY-MM-DD. Defaults to 30 days ago.",
                    "end_date": "YYYY-MM-DD. Defaults to today.",
                    "resolution": "day|week|month. Defaults to day.",
                    "segment_by": "Optional dimension to segment by.",
                },
                "output": "ChartResponse with .primary_values, .primary_dates, .averages()",
            },
            {
                "name": "list_available_charts",
                "description": "Discover all available chart names from the API at runtime.",
                "inputs": {},
                "output": "list[str] of valid chart names",
            },
            {
                "name": "get_health_charts",
                "description": "Pull the 5 key charts for health analysis (MRR, churn, actives, new trials, trial conversion).",
                "inputs": {"days": "Number of days to look back. Default 30."},
                "output": "dict[str, ChartResponse]",
            },
            {
                "name": "analyze_health",
                "description": "Run complete health analysis. Returns health score (0-100), insights with severity levels, and recommendations.",
                "inputs": {
                    "overview": "OverviewMetrics from get_overview(). Optional.",
                    "charts": "dict of chart_name -> ChartResponse from get_health_charts(). Required.",
                },
                "output": "AnalysisReport with .health_score, .insights, .critical_insights, .warnings, .positive_signals",
            },
            {
                "name": "calc_trend",
                "description": "Calculate trend direction and magnitude for a series of values. Returns (change_pct, recent_avg).",
                "inputs": {"values": "list[float]", "window": "Rolling window size. Default 7."},
                "output": "tuple[float, float] — (percent_change, recent_average)",
            },
            {
                "name": "detect_anomalies",
                "description": "Find anomalous data points using z-score method.",
                "inputs": {"values": "list[float]", "threshold": "Standard deviations from mean. Default 2.0."},
                "output": "list[tuple[index, value, direction]] where direction is spike|drop",
            },
            {
                "name": "generate_report",
                "description": "Generate reports in HTML, Markdown, or JSON format.",
                "inputs": {
                    "report": "AnalysisReport from analyze_health().",
                    "formats": "list of html|md|json. Default [html, md].",
                    "output_dir": "Directory to save files. Default ./rc-report.",
                },
                "output": "list[str] of saved file paths",
            },
        ],
        "configuration": {
            "required_env": {"RC_API_KEY": "RevenueCat secret API key (sk_...)"},
            "optional_env": {"RC_PROJECT_ID": "Project ID. Auto-discovered if omitted."},
            "analyzer_thresholds": {
                "description": "All thresholds are configurable via InsightsAnalyzer constructor.",
                "defaults": {
                    "mrr_growth_threshold": 10,
                    "mrr_decline_threshold": -5,
                    "churn_critical": 10,
                    "anomaly_std_threshold": 2.0,
                },
            },
        },
    }
