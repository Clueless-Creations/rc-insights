"""rc-insights CLI — subscription health analysis from the command line.

Usage:
    rc-insights overview              Show current overview metrics
    rc-insights health                Run full health analysis
    rc-insights chart mrr             Pull a specific chart
    rc-insights report --html         Generate HTML dashboard report
    rc-insights report --all          Generate all report formats

Environment:
    RC_API_KEY       Your RevenueCat secret API key (sk_...)
    RC_PROJECT_ID    Your project ID (auto-discovered if omitted)
"""

from __future__ import annotations

import json
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from rc_insights.client import ChartsClient, ChartMetric, Resolution
from rc_insights.analyzer import InsightsAnalyzer, Severity
from rc_insights.report import ReportGenerator

console = Console()


def _get_client(api_key: str | None, project_id: str | None) -> ChartsClient:
    """Create a client, auto-discovering project ID if needed."""
    client = ChartsClient(api_key=api_key, project_id=project_id or "")
    if not client.project_id:
        console.print("[dim]Auto-discovering project ID...[/dim]")
        pid = client.discover_project_id()
        console.print(f"[dim]Found project: {pid}[/dim]")
    return client


@click.group()
@click.option("--api-key", envvar="RC_API_KEY", help="RevenueCat secret API key")
@click.option("--project-id", envvar="RC_PROJECT_ID", help="Project ID (auto-discovered if omitted)")
@click.pass_context
def main(ctx, api_key, project_id):
    """rc-insights: Agent-ready RevenueCat Charts API analysis."""
    ctx.ensure_object(dict)
    ctx.obj["api_key"] = api_key
    ctx.obj["project_id"] = project_id


@main.command()
@click.pass_context
def overview(ctx):
    """Show current overview metrics."""
    with _get_client(ctx.obj["api_key"], ctx.obj["project_id"]) as client:
        metrics = client.get_overview()

    table = Table(title="RevenueCat Overview", show_header=True)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    if metrics.mrr is not None:
        table.add_row("MRR", f"${metrics.mrr:,.2f}")
    if metrics.active_subscriptions is not None:
        table.add_row("Active Subscriptions", f"{int(metrics.active_subscriptions):,}")
    if metrics.active_trials is not None:
        table.add_row("Active Trials", f"{int(metrics.active_trials):,}")
    if metrics.revenue_last_28_days is not None:
        table.add_row("Revenue (28d)", f"${metrics.revenue_last_28_days:,.2f}")
    if metrics.new_customers_last_28_days is not None:
        table.add_row("New Customers (28d)", f"{int(metrics.new_customers_last_28_days):,}")

    console.print(table)


@main.command()
@click.option("--days", default=30, help="Number of days to analyze")
@click.option("--json-output", is_flag=True, help="Output as JSON (agent-friendly)")
@click.pass_context
def health(ctx, days, json_output):
    """Run a full subscription health analysis."""
    with _get_client(ctx.obj["api_key"], ctx.obj["project_id"]) as client:
        console.print("[dim]Fetching overview metrics...[/dim]")
        overview_data = client.get_overview()

        console.print("[dim]Fetching subscriber health charts...[/dim]")
        charts = client.get_subscriber_health(days=days)

        console.print("[dim]Fetching MRR trend...[/dim]")
        mrr_chart = client.get_mrr_trend(days=days)
        charts["mrr"] = mrr_chart

    analyzer = InsightsAnalyzer()
    report = analyzer.analyze_health(overview_data, charts)

    if json_output:
        click.echo(json.dumps(report.to_dict(), indent=2))
        return

    # Rich display
    hs = report.health_score
    score_color = "green" if hs.score >= 80 else "yellow" if hs.score >= 60 else "red"
    console.print(Panel(
        f"[bold {score_color}]{hs.score}/100[/] — Grade {hs.grade}\n{hs.summary}",
        title="Health Score",
    ))

    if report.summary:
        console.print(f"\n{report.summary}\n")

    severity_styles = {
        Severity.CRITICAL: ("red", "🚨"),
        Severity.WARNING: ("yellow", "⚠️"),
        Severity.POSITIVE: ("green", "✅"),
        Severity.INFO: ("dim", "ℹ️"),
    }

    for insight in report.insights:
        style, icon = severity_styles.get(insight.severity, ("dim", "ℹ️"))
        console.print(f"\n{icon} [{style}]{insight.title}[/]")
        console.print(f"  {insight.description}")
        if insight.recommendation:
            console.print(f"  [italic]→ {insight.recommendation}[/italic]")


@main.command()
@click.argument("metric")
@click.option("--days", default=30, help="Number of days")
@click.option("--resolution", type=click.Choice(["day", "week", "month"]), default="day")
@click.option("--segment-by", help="Segment dimension (country, store, product, etc.)")
@click.pass_context
def chart(ctx, metric, days, resolution, segment_by):
    """Pull data for a specific chart metric."""
    with _get_client(ctx.obj["api_key"], ctx.obj["project_id"]) as client:
        result = client.get_chart(
            metric=metric,
            start_date=None,  # Will default to N days ago
            resolution=resolution,
            segment_by=segment_by,
        )

    table = Table(title=f"Chart: {metric}", show_header=True)
    table.add_column("Date")
    table.add_column("Value", justify="right")
    if result.segments:
        table.add_column("Segment")

    for dp in result.data_points:
        row = [dp.date, f"{dp.value:,.2f}"]
        if result.segments:
            row.append(dp.segment or "—")
        table.add_row(*row)

    console.print(table)


@main.command()
@click.option("--days", default=30, help="Number of days to analyze")
@click.option("--html", "fmt_html", is_flag=True, help="Generate HTML report")
@click.option("--markdown", "fmt_md", is_flag=True, help="Generate Markdown report")
@click.option("--json-out", "fmt_json", is_flag=True, help="Generate JSON report")
@click.option("--all", "fmt_all", is_flag=True, help="Generate all formats")
@click.option("--output-dir", default="./rc-report", help="Output directory")
@click.pass_context
def report(ctx, days, fmt_html, fmt_md, fmt_json, fmt_all, output_dir):
    """Generate health report in various formats."""
    formats = []
    if fmt_all:
        formats = ["html", "md", "json"]
    else:
        if fmt_html:
            formats.append("html")
        if fmt_md:
            formats.append("md")
        if fmt_json:
            formats.append("json")
    if not formats:
        formats = ["html", "md"]  # Default

    with _get_client(ctx.obj["api_key"], ctx.obj["project_id"]) as client:
        console.print("[dim]Fetching data...[/dim]")
        overview_data = client.get_overview()
        charts = client.get_subscriber_health(days=days)
        charts["mrr"] = client.get_mrr_trend(days=days)

    analyzer = InsightsAnalyzer()
    analysis = analyzer.analyze_health(overview_data, charts)

    generator = ReportGenerator()
    saved = generator.save(analysis, output_dir=output_dir, formats=formats)

    for path in saved:
        console.print(f"[green]✓[/green] Saved: {path}")


if __name__ == "__main__":
    main()
