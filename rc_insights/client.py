"""RevenueCat Charts API client — zero external dependencies.

Uses only Python stdlib (urllib, json, dataclasses).
Built from actual V2 Charts API responses.
"""

from __future__ import annotations

import json
import os
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional


class ChartName(str, Enum):
    """Available chart names in RevenueCat Charts API V2."""
    ACTIVES = "actives"
    ACTIVES_MOVEMENT = "actives_movement"
    ACTIVES_NEW = "actives_new"
    ARR = "arr"
    CHURN = "churn"
    COHORT_EXPLORER = "cohort_explorer"
    CONVERSION_TO_PAYING = "conversion_to_paying"
    CUSTOMERS_ACTIVE = "customers_active"
    CUSTOMERS_NEW = "customers_new"
    LTV_PER_CUSTOMER = "ltv_per_customer"
    LTV_PER_PAYING_CUSTOMER = "ltv_per_paying_customer"
    MRR = "mrr"
    MRR_MOVEMENT = "mrr_movement"
    REFUND_RATE = "refund_rate"
    REVENUE = "revenue"
    SUBSCRIPTION_RETENTION = "subscription_retention"
    SUBSCRIPTION_STATUS = "subscription_status"
    TRIALS = "trials"
    TRIALS_MOVEMENT = "trials_movement"
    TRIALS_NEW = "trials_new"
    TRIAL_CONVERSION_RATE = "trial_conversion_rate"


class Resolution(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


@dataclass
class ChartDataPoint:
    """A single data point from a chart response."""
    date_ts: int
    date_str: str
    measure_index: int
    value: float
    incomplete: bool = False

    @classmethod
    def from_api(cls, raw: dict) -> "ChartDataPoint":
        ts = raw.get("cohort", 0)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return cls(
            date_ts=ts,
            date_str=dt.strftime("%Y-%m-%d"),
            measure_index=raw.get("measure", 0),
            value=float(raw.get("value", 0)),
            incomplete=raw.get("incomplete", False),
        )


@dataclass
class ChartMeasure:
    """Describes a measure (metric) within a chart."""
    display_name: str
    description: str
    unit: str
    chartable: bool
    decimal_precision: int


@dataclass
class ChartResponse:
    """Parsed response from a Charts API query."""
    chart_name: str
    display_name: str
    description: str
    category: str
    resolution: str
    start_date: int
    end_date: int
    measures: list[ChartMeasure] = field(default_factory=list)
    data_points: list[ChartDataPoint] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, chart_name: str, raw: dict) -> "ChartResponse":
        measures = []
        for m in raw.get("measures", []):
            measures.append(ChartMeasure(
                display_name=m.get("display_name", ""),
                description=m.get("description", ""),
                unit=m.get("unit", ""),
                chartable=m.get("chartable", True),
                decimal_precision=m.get("decimal_precision", 0),
            ))
        data_points = [ChartDataPoint.from_api(dp) for dp in raw.get("values", []) if isinstance(dp, dict)]

        return cls(
            chart_name=chart_name,
            display_name=raw.get("display_name", ""),
            description=raw.get("description", ""),
            category=raw.get("category", ""),
            resolution=raw.get("resolution", "day"),
            start_date=raw.get("start_date", 0),
            end_date=raw.get("end_date", 0),
            measures=measures,
            data_points=data_points,
            summary=raw.get("summary", {}),
            raw=raw,
        )

    def values_for_measure(self, measure_index: int = 0) -> list[float]:
        """Extract values for a specific measure index."""
        return [dp.value for dp in self.data_points if dp.measure_index == measure_index]

    def dates_for_measure(self, measure_index: int = 0) -> list[str]:
        """Extract dates for a specific measure index."""
        return [dp.date_str for dp in self.data_points if dp.measure_index == measure_index]

    @property
    def primary_values(self) -> list[float]:
        """Values for the first chartable measure."""
        for i, m in enumerate(self.measures):
            if m.chartable:
                return self.values_for_measure(i)
        return self.values_for_measure(0)

    @property
    def primary_dates(self) -> list[str]:
        for i, m in enumerate(self.measures):
            if m.chartable:
                return self.dates_for_measure(i)
        return self.dates_for_measure(0)

    @property
    def primary_measure_name(self) -> str:
        for m in self.measures:
            if m.chartable:
                return m.display_name
        return self.measures[0].display_name if self.measures else ""

    def averages(self) -> dict[str, float]:
        return self.summary.get("average", {})


@dataclass
class OverviewMetric:
    id: str
    name: str
    value: float
    unit: str
    description: str
    period: str


@dataclass
class OverviewMetrics:
    """Current overview metrics snapshot."""
    metrics: list[OverviewMetric] = field(default_factory=list)
    raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, raw: dict) -> "OverviewMetrics":
        metrics = []
        for m in raw.get("metrics", []):
            metrics.append(OverviewMetric(
                id=m.get("id", ""),
                name=m.get("name", ""),
                value=float(m.get("value", 0)),
                unit=m.get("unit", ""),
                description=m.get("description", ""),
                period=m.get("period", ""),
            ))
        return cls(metrics=metrics, raw=raw)

    def get(self, metric_id: str) -> Optional[float]:
        for m in self.metrics:
            if m.id == metric_id:
                return m.value
        return None

    @property
    def mrr(self) -> Optional[float]: return self.get("mrr")
    @property
    def active_subscriptions(self) -> Optional[float]: return self.get("active_subscriptions")
    @property
    def active_trials(self) -> Optional[float]: return self.get("active_trials")
    @property
    def revenue(self) -> Optional[float]: return self.get("revenue")
    @property
    def new_customers(self) -> Optional[float]: return self.get("new_customers")
    @property
    def active_users(self) -> Optional[float]: return self.get("active_users")


class ChartsClient:
    """RevenueCat Charts API V2 client — zero dependencies.

    Usage:
        client = ChartsClient()  # reads RC_API_KEY from env
        overview = client.get_overview()
        mrr = client.get_chart("mrr", start_date="2026-01-01")
    """

    BASE_URL = "https://api.revenuecat.com/v2"

    def __init__(self, api_key: Optional[str] = None, project_id: Optional[str] = None):
        self.api_key = api_key or os.environ.get("RC_API_KEY", "")
        self.project_id = project_id or os.environ.get("RC_PROJECT_ID", "")
        if not self.api_key:
            raise ValueError("API key required. Set RC_API_KEY or pass api_key=")

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self.BASE_URL}{path}"
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
            if qs:
                url += f"?{qs}"
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"RevenueCat API {e.code}: {body}") from e

    def discover_project_id(self) -> str:
        projects = self._get("/projects").get("items", [])
        if not projects:
            raise ValueError("No projects found for this API key.")
        self.project_id = projects[0]["id"]
        return self.project_id

    def get_overview(self) -> OverviewMetrics:
        if not self.project_id:
            self.discover_project_id()
        return OverviewMetrics.from_api(
            self._get(f"/projects/{self.project_id}/metrics/overview")
        )

    def get_chart(
        self,
        chart_name: ChartName | str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        resolution: str = "day",
        segment_by: Optional[str] = None,
    ) -> ChartResponse:
        if not self.project_id:
            self.discover_project_id()
        name = chart_name.value if isinstance(chart_name, ChartName) else chart_name
        if not start_date:
            start_date = (date.today() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = date.today().isoformat()
        params: dict[str, Any] = {"start_date": start_date, "end_date": end_date, "resolution": resolution}
        if segment_by:
            params["segment_by"] = segment_by
        data = self._get(f"/projects/{self.project_id}/charts/{name}", params)
        return ChartResponse.from_api(name, data)

    def get_health_charts(self, days: int = 30) -> dict[str, ChartResponse]:
        start = (date.today() - timedelta(days=days)).isoformat()
        charts = {}
        for name in [ChartName.MRR, ChartName.CHURN, ChartName.ACTIVES,
                      ChartName.TRIALS_NEW, ChartName.TRIAL_CONVERSION_RATE]:
            charts[name.value] = self.get_chart(name, start_date=start)
        return charts
