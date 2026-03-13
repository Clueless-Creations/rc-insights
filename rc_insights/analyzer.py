"""Insights analyzer — turns chart data into actionable intelligence."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from rc_insights.client import ChartResponse, OverviewMetrics


class Severity(str, Enum):
    INFO = "info"
    POSITIVE = "positive"
    WARNING = "warning"
    CRITICAL = "critical"


class InsightCategory(str, Enum):
    REVENUE = "revenue"
    GROWTH = "growth"
    RETENTION = "retention"
    CONVERSION = "conversion"
    ANOMALY = "anomaly"


@dataclass
class Insight:
    title: str
    description: str
    severity: Severity
    category: InsightCategory
    metric_name: str
    current_value: Optional[float] = None
    previous_value: Optional[float] = None
    change_pct: Optional[float] = None
    recommendation: Optional[str] = None

    def to_dict(self) -> dict:
        return {k: (v.value if isinstance(v, Enum) else v) for k, v in self.__dict__.items()}


@dataclass
class HealthScore:
    score: int
    grade: str
    summary: str = ""

    def to_dict(self) -> dict:
        return {"score": self.score, "grade": self.grade, "summary": self.summary}


@dataclass
class AnalysisReport:
    health_score: HealthScore
    insights: list[Insight] = field(default_factory=list)
    summary: str = ""
    generated_at: str = ""

    @property
    def critical_insights(self) -> list[Insight]:
        return [i for i in self.insights if i.severity == Severity.CRITICAL]

    @property
    def warnings(self) -> list[Insight]:
        return [i for i in self.insights if i.severity == Severity.WARNING]

    @property
    def positive_signals(self) -> list[Insight]:
        return [i for i in self.insights if i.severity == Severity.POSITIVE]

    def to_dict(self) -> dict:
        return {
            "health_score": self.health_score.to_dict(),
            "insights": [i.to_dict() for i in self.insights],
            "summary": self.summary,
            "critical_count": len(self.critical_insights),
            "warning_count": len(self.warnings),
            "positive_count": len(self.positive_signals),
            "generated_at": self.generated_at,
        }


class InsightsAnalyzer:
    """Analyzes RevenueCat chart data and produces actionable insights.
    
    Thresholds are configurable so agents can adjust sensitivity:
        analyzer = InsightsAnalyzer(churn_critical=12, mrr_growth_threshold=8)
    """

    def __init__(
        self,
        mrr_growth_threshold: float = 10,
        mrr_decline_threshold: float = -5,
        mrr_critical_decline: float = -15,
        churn_critical: float = 10,
        churn_increase_threshold: float = 20,
        churn_improve_threshold: float = -10,
        trial_surge_threshold: float = 15,
        trial_decline_threshold: float = -15,
        trial_conversion_low: float = 20,
        trial_conversion_high: float = 40,
        actives_growth_threshold: float = 5,
        anomaly_std_threshold: float = 2.0,
    ):
        self.mrr_growth_threshold = mrr_growth_threshold
        self.mrr_decline_threshold = mrr_decline_threshold
        self.mrr_critical_decline = mrr_critical_decline
        self.churn_critical = churn_critical
        self.churn_increase_threshold = churn_increase_threshold
        self.churn_improve_threshold = churn_improve_threshold
        self.trial_surge_threshold = trial_surge_threshold
        self.trial_decline_threshold = trial_decline_threshold
        self.trial_conversion_low = trial_conversion_low
        self.trial_conversion_high = trial_conversion_high
        self.actives_growth_threshold = actives_growth_threshold
        self.anomaly_std_threshold = anomaly_std_threshold

    @staticmethod
    def calc_trend(values: list[float], window: int = 7) -> tuple[float, float]:
        """(change_pct, recent_avg) using rolling window comparison."""
        if len(values) < 2:
            return 0.0, values[-1] if values else 0.0
        if len(values) < window * 2:
            window = max(1, len(values) // 2)
        recent = sum(values[-window:]) / window
        previous = sum(values[-window * 2:-window]) / window
        if previous == 0:
            return 0.0, recent
        return ((recent - previous) / abs(previous)) * 100, recent

    @staticmethod
    def detect_anomalies(values: list[float], threshold: float = 2.0) -> list[tuple[int, float, str]]:
        if len(values) < 10:
            return []
        mean = sum(values) / len(values)
        std = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
        if std == 0:
            return []
        return [(i, v, "spike" if (v - mean) / std > 0 else "drop")
                for i, v in enumerate(values) if abs((v - mean) / std) > threshold]

    def _analyze_mrr(self, chart: ChartResponse) -> list[Insight]:
        insights = []
        values = chart.primary_values
        if not values:
            return insights
        change, current = self.calc_trend(values)
        if change > self.mrr_growth_threshold:
            insights.append(Insight("MRR Growing Strong", f"MRR up {change:.1f}% recently. Current ~${current:,.0f}.",
                                    Severity.POSITIVE, InsightCategory.REVENUE, "mrr", current, change_pct=change,
                                    recommendation="Monetization is working. Consider investing more in acquisition."))
        elif change < self.mrr_decline_threshold:
            sev = Severity.CRITICAL if change < self.mrr_critical_decline else Severity.WARNING
            insights.append(Insight("MRR Declining", f"MRR down {abs(change):.1f}%. Current ~${current:,.0f}.",
                                    sev, InsightCategory.REVENUE, "mrr", current, change_pct=change,
                                    recommendation="Investigate churn drivers. Check app updates, pricing changes, or store issues."))
        for idx, val, direction in self.detect_anomalies(values)[-3:]:
            dates = chart.primary_dates
            d = dates[idx] if idx < len(dates) else f"point {idx}"
            insights.append(Insight(f"MRR Anomaly: {direction.title()} on {d}",
                                    f"Unusual MRR {direction}: ${val:,.0f} on {d}.",
                                    Severity.WARNING, InsightCategory.ANOMALY, "mrr", val))
        return insights

    def _analyze_churn(self, chart: ChartResponse) -> list[Insight]:
        insights = []
        # Churn chart: measure 2 is "Churn Rate" (chartable)
        values = chart.primary_values
        if not values:
            return insights
        change, current = self.calc_trend(values)
        avg = sum(values) / len(values)
        if avg > self.churn_critical:
            insights.append(Insight("High Churn Rate", f"Average churn is {avg:.1f}%, above healthy threshold.",
                                    Severity.CRITICAL, InsightCategory.RETENTION, "churn", current,
                                    recommendation="Prioritize retention: improve onboarding, add rescue offers, check involuntary churn."))
        elif change > self.churn_increase_threshold:
            insights.append(Insight("Churn Trending Up", f"Churn rate trending up {change:.1f}% period-over-period.",
                                    Severity.WARNING, InsightCategory.RETENTION, "churn", current, change_pct=change,
                                    recommendation="Check recent app changes and store reviews for cancellation patterns."))
        elif change < self.churn_improve_threshold:
            insights.append(Insight("Churn Improving", f"Churn trending down {abs(change):.1f}% — retention improving.",
                                    Severity.POSITIVE, InsightCategory.RETENTION, "churn", current, change_pct=change))
        return insights

    def _analyze_trials(self, trials: Optional[ChartResponse], conversion: Optional[ChartResponse]) -> list[Insight]:
        insights = []
        if trials:
            values = trials.primary_values
            if values:
                change, current = self.calc_trend(values)
                if change > self.trial_surge_threshold:
                    insights.append(Insight("Trial Starts Surging", f"New trials up {change:.1f}%. Strong top-of-funnel.",
                                            Severity.POSITIVE, InsightCategory.GROWTH, "trials_new", current, change_pct=change))
                elif change < self.trial_decline_threshold:
                    insights.append(Insight("Trial Starts Declining", f"New trials down {abs(change):.1f}%.",
                                            Severity.WARNING, InsightCategory.GROWTH, "trials_new", current, change_pct=change,
                                            recommendation="Review paywall conversion, ASO, and ad campaigns."))
        if conversion:
            values = conversion.primary_values
            if values:
                avg = sum(values) / len(values)
                if avg > 0 and avg < self.trial_conversion_low:
                    insights.append(Insight("Low Trial Conversion", f"Trial conversion averaging {avg:.1f}%.",
                                            Severity.WARNING, InsightCategory.CONVERSION, "trial_conversion", avg,
                                            recommendation="Optimize trial experience: onboarding, value reminders, trial length."))
                elif avg >= self.trial_conversion_high:
                    insights.append(Insight("Strong Trial Conversion", f"Trial conversion at {avg:.1f}% — excellent.",
                                            Severity.POSITIVE, InsightCategory.CONVERSION, "trial_conversion", avg))
        return insights

    def _analyze_actives(self, chart: ChartResponse) -> list[Insight]:
        insights = []
        values = chart.primary_values
        if not values:
            return insights
        change, current = self.calc_trend(values)
        if change > self.actives_growth_threshold:
            insights.append(Insight("Subscriber Base Growing", f"Active subscriptions up {change:.1f}%.",
                                    Severity.POSITIVE, InsightCategory.GROWTH, "actives", current, change_pct=change))
        elif change < -self.actives_growth_threshold:
            insights.append(Insight("Subscriber Base Shrinking", f"Active subscriptions down {abs(change):.1f}%.",
                                    Severity.WARNING, InsightCategory.GROWTH, "actives", current, change_pct=change,
                                    recommendation="Churn may be outpacing acquisition. Focus retention before scaling."))
        return insights

    def analyze_health(self, overview: Optional[OverviewMetrics], charts: dict[str, ChartResponse]) -> AnalysisReport:
        insights: list[Insight] = []
        if "mrr" in charts:
            insights.extend(self._analyze_mrr(charts["mrr"]))
        if "churn" in charts:
            insights.extend(self._analyze_churn(charts["churn"]))
        insights.extend(self._analyze_trials(charts.get("trials_new"), charts.get("trial_conversion_rate")))
        if "actives" in charts:
            insights.extend(self._analyze_actives(charts["actives"]))

        # Health score
        score = 70
        for i in insights:
            if i.severity == Severity.CRITICAL: score -= 15
            elif i.severity == Severity.WARNING: score -= 5
            elif i.severity == Severity.POSITIVE: score += 5
        score = max(0, min(100, score))
        grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"

        critical = [i for i in insights if i.severity == Severity.CRITICAL]
        positive = [i for i in insights if i.severity == Severity.POSITIVE]
        parts = []
        if critical: parts.append(f"{len(critical)} critical issue(s)")
        if positive: parts.append(f"{len(positive)} positive signal(s)")
        hs_summary = ". ".join(parts) + "." if parts else "No significant changes."

        summary_parts = [f"Health Score: {score}/100 (Grade {grade})."]
        if overview:
            if overview.mrr is not None: summary_parts.append(f"MRR: ${overview.mrr:,.0f}.")
            if overview.active_subscriptions is not None: summary_parts.append(f"Active subs: {int(overview.active_subscriptions):,}.")
            if overview.active_trials is not None: summary_parts.append(f"Active trials: {int(overview.active_trials):,}.")

        return AnalysisReport(
            health_score=HealthScore(score=score, grade=grade, summary=hs_summary),
            insights=insights,
            summary=" ".join(summary_parts),
            generated_at=datetime.now(timezone.utc).isoformat(),
        )
