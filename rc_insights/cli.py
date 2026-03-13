"""rc-insights CLI — subscription health analysis from the command line.

Usage:
    python -m rc_insights overview
    python -m rc_insights health
    python -m rc_insights health --json
    python -m rc_insights chart mrr --days 90
    python -m rc_insights report --output-dir ./my-report
    python -m rc_insights discover

Environment:
    RC_API_KEY       RevenueCat secret API key (sk_...)
    RC_PROJECT_ID    Project ID (auto-discovered if omitted)
"""

from __future__ import annotations

import argparse
import json
import sys

from rc_insights.client import ChartsClient, ChartName
from rc_insights.analyzer import InsightsAnalyzer, Severity
from rc_insights.report import ReportGenerator


def cmd_overview(client: ChartsClient, args):
    """Show current overview metrics."""
    overview = client.get_overview()
    print("RevenueCat Overview")
    print("=" * 40)
    for m in overview.metrics:
        if m.unit == "$":
            print(f"  {m.name}: ${m.value:,.0f}")
        elif m.unit == "#":
            print(f"  {m.name}: {int(m.value):,}")
        else:
            print(f"  {m.name}: {m.value}")


def cmd_health(client: ChartsClient, args):
    """Run full health analysis."""
    overview = client.get_overview()
    charts = client.get_health_charts(days=args.days)

    analyzer = InsightsAnalyzer()
    report = analyzer.analyze_health(overview, charts)

    if args.json_output:
        print(json.dumps(report.to_dict(), indent=2, default=str))
        return

    hs = report.health_score
    print(f"\n  Health Score: {hs.score}/100 — Grade {hs.grade}")
    print(f"  {hs.summary}\n")
    print(report.summary)

    icons = {"critical": "🚨", "warning": "⚠️ ", "positive": "✅", "info": "ℹ️ "}
    for insight in report.insights:
        icon = icons.get(insight.severity.value, "•")
        print(f"\n{icon} {insight.title}")
        print(f"  {insight.description}")
        if insight.recommendation:
            print(f"  → {insight.recommendation}")


def cmd_chart(client: ChartsClient, args):
    """Pull a specific chart."""
    from datetime import date, timedelta

    start = (date.today() - timedelta(days=args.days)).isoformat()
    chart = client.get_chart(args.chart_name, start_date=start, resolution=args.resolution)

    print(f"Chart: {chart.display_name or chart.chart_name}")
    print(f"Resolution: {chart.resolution}")
    print(f"Data points: {len(chart.data_points)}")
    print()

    dates = chart.primary_dates
    values = chart.primary_values
    for d, v in zip(dates, values):
        print(f"  {d}  {v:>12,.2f}")


def cmd_report(client: ChartsClient, args):
    """Generate reports."""
    overview = client.get_overview()
    charts = client.get_health_charts(days=args.days)

    analyzer = InsightsAnalyzer()
    report = analyzer.analyze_health(overview, charts)

    generator = ReportGenerator()
    saved = generator.save(report, output_dir=args.output_dir, formats=["html", "md", "json"])
    for path in saved:
        print(f"✓ Saved: {path}")


def cmd_discover(client: ChartsClient, args):
    """Discover available charts."""
    charts = client.list_available_charts()
    print(f"Available charts ({len(charts)}):")
    for name in charts:
        print(f"  {name}")


def main():
    parser = argparse.ArgumentParser(
        prog="rc-insights",
        description="Agent-ready RevenueCat Charts API analysis",
    )
    parser.add_argument("--api-key", help="RevenueCat secret API key")
    parser.add_argument("--project-id", help="Project ID (auto-discovered if omitted)")

    sub = parser.add_subparsers(dest="command", help="Command")

    sub.add_parser("overview", help="Show current overview metrics")

    health_p = sub.add_parser("health", help="Run full health analysis")
    health_p.add_argument("--days", type=int, default=30, help="Days to analyze")
    health_p.add_argument("--json", dest="json_output", action="store_true", help="Output as JSON")

    chart_p = sub.add_parser("chart", help="Pull a specific chart")
    chart_p.add_argument("chart_name", help="Chart name (use 'discover' to list)")
    chart_p.add_argument("--days", type=int, default=30, help="Days to look back")
    chart_p.add_argument("--resolution", default="day", choices=["day", "week", "month"])

    report_p = sub.add_parser("report", help="Generate reports")
    report_p.add_argument("--days", type=int, default=30, help="Days to analyze")
    report_p.add_argument("--output-dir", default="./rc-report", help="Output directory")

    sub.add_parser("discover", help="List available chart types")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    client = ChartsClient(api_key=args.api_key, project_id=args.project_id or "")
    if not client.project_id:
        client.discover_project_id()

    commands = {
        "overview": cmd_overview,
        "health": cmd_health,
        "chart": cmd_chart,
        "report": cmd_report,
        "discover": cmd_discover,
    }
    commands[args.command](client, args)


if __name__ == "__main__":
    main()
