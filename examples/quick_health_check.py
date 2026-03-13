#!/usr/bin/env python3
"""Quick health check — the simplest way to use rc-insights.

Run: RC_API_KEY=sk_... python quick_health_check.py
"""

from rc_insights import ChartsClient, InsightsAnalyzer, ReportGenerator


def main():
    # Connect to RevenueCat Charts API
    client = ChartsClient()  # Reads RC_API_KEY and RC_PROJECT_ID from env
    
    # Auto-discover project if ID not set
    if not client.project_id:
        client.discover_project_id()
        print(f"Discovered project: {client.project_id}")

    # Pull overview metrics
    overview = client.get_overview()
    print(f"Current MRR: ${overview.mrr:,.2f}")
    print(f"Active Subs: {overview.active_subscriptions:,.0f}")

    # Pull health charts (active subs, churn, trials, conversion)
    charts = client.get_subscriber_health(days=30)
    charts["mrr"] = client.get_mrr_trend(days=90)

    # Analyze
    analyzer = InsightsAnalyzer()
    report = analyzer.analyze_health(overview, charts)

    print(f"\nHealth Score: {report.health_score.score}/100 (Grade {report.health_score.grade})")
    print(f"Summary: {report.summary}")

    for insight in report.insights:
        icon = {"critical": "🚨", "warning": "⚠️", "positive": "✅", "info": "ℹ️"}
        print(f"\n{icon.get(insight.severity.value, '•')} {insight.title}")
        print(f"  {insight.description}")
        if insight.recommendation:
            print(f"  → {insight.recommendation}")

    # Generate reports
    generator = ReportGenerator()
    saved = generator.save(report, output_dir="./my-report", formats=["html", "md", "json"])
    print(f"\nReports saved: {saved}")


if __name__ == "__main__":
    main()
