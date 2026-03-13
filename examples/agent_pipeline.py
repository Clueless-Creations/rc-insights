#!/usr/bin/env python3
"""Agent pipeline example — how an autonomous agent uses rc-insights.

This shows how an AI agent can:
1. Pull subscription metrics programmatically
2. Analyze them for actionable insights
3. Make decisions based on the results
4. Output structured data for downstream processing

Run: RC_API_KEY=sk_... python agent_pipeline.py
"""

import json
from rc_insights import ChartsClient, InsightsAnalyzer
from rc_insights.client import ChartMetric, SegmentDimension


def main():
    client = ChartsClient()  # From env vars
    if not client.project_id:
        client.discover_project_id()

    # ── Step 1: Pull the data an agent needs for daily operations ──
    
    overview = client.get_overview()
    
    # Health metrics
    health_charts = client.get_subscriber_health(days=30)
    health_charts["mrr"] = client.get_mrr_trend(days=90)
    
    # Revenue by product (to identify top performers)
    revenue_by_product = client.get_revenue_breakdown(
        days=30, segment_by=SegmentDimension.PRODUCT
    )
    
    # Revenue by country (to identify growth markets)
    revenue_by_country = client.get_revenue_breakdown(
        days=30, segment_by=SegmentDimension.COUNTRY
    )

    # ── Step 2: Analyze ──
    
    analyzer = InsightsAnalyzer()
    report = analyzer.analyze_health(overview, health_charts)

    # ── Step 3: Agent decision logic ──
    
    decisions = []
    
    for insight in report.insights:
        if insight.severity.value == "critical":
            decisions.append({
                "action": "alert_operator",
                "priority": "high",
                "reason": insight.title,
                "detail": insight.description,
            })
        elif insight.severity.value == "warning" and insight.category.value == "retention":
            decisions.append({
                "action": "investigate_churn",
                "priority": "medium",
                "reason": insight.title,
                "recommendation": insight.recommendation,
            })
        elif insight.severity.value == "positive" and insight.category.value == "growth":
            decisions.append({
                "action": "scale_acquisition",
                "priority": "low",
                "reason": insight.title,
            })

    # ── Step 4: Structured output for the agent's next step ──
    
    output = {
        "timestamp": report.generated_at,
        "health_score": report.health_score.to_dict(),
        "overview": {
            "mrr": overview.mrr,
            "active_subscriptions": overview.active_subscriptions,
            "active_trials": overview.active_trials,
        },
        "insights_count": {
            "critical": len(report.critical_insights),
            "warnings": len(report.warnings),
            "positive": len(report.positive_signals),
        },
        "agent_decisions": decisions,
    }
    
    print(json.dumps(output, indent=2, default=str))
    
    # An agent would now feed this into its next decision:
    # - Post a daily report to Slack/Discord
    # - Trigger a win-back campaign if churn is critical
    # - Adjust ad spend if growth signals are strong
    # - Log to its memory for trend tracking across sessions


if __name__ == "__main__":
    main()
