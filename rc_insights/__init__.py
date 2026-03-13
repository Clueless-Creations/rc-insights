"""rc-insights: Agent-ready RevenueCat Charts API analysis toolkit."""

__version__ = "0.2.0"

from rc_insights.client import ChartsClient, ChartName, ChartResponse, OverviewMetrics, Resolution
from rc_insights.analyzer import InsightsAnalyzer, AnalysisReport, Insight, Severity, InsightCategory, HealthScore
from rc_insights.report import ReportGenerator

__all__ = [
    "ChartsClient", "ChartName", "ChartResponse", "OverviewMetrics", "Resolution",
    "InsightsAnalyzer", "AnalysisReport", "Insight", "Severity", "InsightCategory", "HealthScore",
    "ReportGenerator",
]
