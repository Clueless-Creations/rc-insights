"""rc-insights: Agent-ready RevenueCat Charts API analysis toolkit."""

__version__ = "0.1.0"

from rc_insights.client import ChartsClient
from rc_insights.analyzer import InsightsAnalyzer
from rc_insights.report import ReportGenerator

__all__ = ["ChartsClient", "InsightsAnalyzer", "ReportGenerator"]
