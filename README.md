# rc-insights

**Agent-ready subscription analytics for RevenueCat's Charts API.**

`rc-insights` is a Python CLI and library that turns RevenueCat Charts API data into actionable intelligence. Built for both human developers and autonomous AI agents.

> **Disclosure:** rc-insights was built by [Katire](https://clueless.clothing/katire-revenuecat-application/), an autonomous AI agent, as part of a RevenueCat take-home assignment. The tool is fully functional and open source.

## Why rc-insights?

RevenueCat's Charts API gives you raw subscription metrics. That's powerful, but most developers need *insights*, not data points. rc-insights bridges that gap:

- **Health Scoring** — Get a 0-100 health score for your subscription business with letter grades
- **Trend Detection** — Automatic identification of growth, decline, and stagnation patterns
- **Anomaly Flagging** — Z-score-based detection of unusual spikes or drops in your metrics
- **Strategic Recommendations** — Each insight comes with an actionable next step
- **Multi-Format Reports** — HTML dashboard, Markdown (for Notion/GitHub), and JSON (for agent pipelines)

## Quick Start

### Install

```bash
pip install rc-insights
```

### Set Up

```bash
export RC_API_KEY="sk_your_secret_key_here"
export RC_PROJECT_ID="proj_your_project_id"  # Optional — auto-discovered
```

### CLI Usage

```bash
# See current overview metrics
rc-insights overview

# Run a full health analysis
rc-insights health

# Get analysis as JSON (agent-friendly)
rc-insights health --json-output

# Pull a specific chart
rc-insights chart mrr --days 90

# Generate reports
rc-insights report --all --output-dir ./my-report
```

### Python Library

```python
from rc_insights import ChartsClient, InsightsAnalyzer, ReportGenerator

# Connect
client = ChartsClient()  # Reads from env vars
if not client.project_id:
    client.discover_project_id()

# Pull data
overview = client.get_overview()
charts = client.get_subscriber_health(days=30)
charts["mrr"] = client.get_mrr_trend(days=90)

# Analyze
analyzer = InsightsAnalyzer()
report = analyzer.analyze_health(overview, charts)

print(f"Health: {report.health_score.score}/100 ({report.health_score.grade})")

for insight in report.insights:
    print(f"  {insight.severity.value}: {insight.title}")

# Generate HTML dashboard
generator = ReportGenerator()
generator.save(report, formats=["html", "md", "json"])
```

## For AI Agents

rc-insights is designed for agent consumption. The `--json-output` flag and `to_dict()` methods output structured data that agents can parse and act on:

```python
# In your agent's daily operations
report = analyzer.analyze_health(overview, charts)

# Check if any critical issues need operator attention
if report.critical_insights:
    notify_operator(report.critical_insights)

# Use structured output in your agent pipeline
data = report.to_dict()
# → {"health_score": {"score": 82, "grade": "B"}, "insights": [...]}
```

See [examples/agent_pipeline.py](examples/agent_pipeline.py) for a full agent integration example.

## Available Metrics

| Metric | CLI Name | Description |
|--------|----------|-------------|
| MRR | `mrr` | Monthly Recurring Revenue |
| ARR | `arr` | Annual Recurring Revenue |
| Revenue | `revenue` | Gross revenue |
| Active Subscriptions | `active_subscriptions` | Current paid subscribers |
| Active Trials | `active_trials` | Current active trials |
| Churn | `churn` | Subscription churn rate |
| New Customers | `new_customers` | New customer count |
| New Trials | `new_trials` | New trial starts |
| Trial Conversion | `trial_conversion` | Trial to paid conversion rate |
| New Paid Subs | `new_paid_subscriptions` | New paid subscription starts |
| Realized LTV | `realized_ltv_per_customer` | Lifetime value per customer |
| Refund Rate | `refund_rate` | Refund rate |
| Retention | `subscription_retention` | Subscription retention |

## Segmentation

Segment any chart by:
- **Country** — Compare performance across markets
- **Store** — App Store vs Play Store vs Stripe
- **Product** — Compare subscription tiers
- **Product Duration** — Monthly vs annual
- **Offering** — Compare offering performance

```bash
rc-insights chart revenue --segment-by country --days 30
```

## Report Formats

### HTML Dashboard
A self-contained, dark-themed HTML report with health score, insights, and recommendations. Drop it in a browser or serve it from your CI.

### Markdown
Perfect for posting to Notion pages, GitHub issues, or Slack. Structured with headers and emoji for readability.

### JSON
Machine-readable output for agent pipelines, dashboards, and automated workflows.

## Examples

- [quick_health_check.py](examples/quick_health_check.py) — Simplest usage
- [agent_pipeline.py](examples/agent_pipeline.py) — Full agent integration
- [daily_slack_report.py](examples/daily_slack_report.py) — Daily Slack notifications

## Architecture

```
rc_insights/
├── client.py      # Charts API client with typed responses
├── analyzer.py    # Insight engine (trends, anomalies, scoring)
├── report.py      # Multi-format report generation
└── cli.py         # Click-based CLI interface
```

The client layer handles API communication and response parsing. The analyzer transforms raw data into insights using trend analysis and anomaly detection. The report generator produces human and machine-readable outputs.

## Requirements

- Python 3.9+
- `httpx` — HTTP client
- `rich` — Terminal UI
- `click` — CLI framework
- `jinja2` — Template engine

## License

MIT

## Credits

Built by [Katire](https://clueless.clothing/katire-revenuecat-application/) — an autonomous AI agent running on [OpenClaw](https://github.com/openclaw/openclaw).

Powered by the [RevenueCat Charts API](https://www.revenuecat.com/docs/dashboard-and-metrics/charts).
