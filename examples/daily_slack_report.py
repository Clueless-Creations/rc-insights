#!/usr/bin/env python3
"""Daily Slack report — post a subscription health summary to Slack.

Run this on a daily cron to keep your team informed.

Required env vars:
    RC_API_KEY       RevenueCat secret API key
    RC_PROJECT_ID    Project ID (optional, auto-discovered)
    SLACK_WEBHOOK    Slack incoming webhook URL
"""

import json
import os
import httpx
from rc_insights import ChartsClient, InsightsAnalyzer


def format_slack_message(report) -> dict:
    """Format the analysis report as a Slack Block Kit message."""
    hs = report.health_score
    
    # Emoji based on grade
    grade_emoji = {"A": "🟢", "B": "🟢", "C": "🟡", "D": "🟠", "F": "🔴"}.get(hs.grade, "⚪")
    
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"{grade_emoji} Daily Subscription Health: {hs.score}/100"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": report.summary}
        },
        {"type": "divider"},
    ]
    
    # Add critical issues
    for insight in report.critical_insights:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"🚨 *{insight.title}*\n{insight.description}"}
        })
    
    # Add warnings (max 3)
    for insight in report.warnings[:3]:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"⚠️ *{insight.title}*\n{insight.description}"}
        })
    
    # Add positive signals (max 2)
    for insight in report.positive_signals[:2]:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"✅ *{insight.title}*\n{insight.description}"}
        })
    
    return {"blocks": blocks}


def main():
    # Analyze
    client = ChartsClient()
    if not client.project_id:
        client.discover_project_id()
    
    overview = client.get_overview()
    charts = client.get_subscriber_health(days=30)
    charts["mrr"] = client.get_mrr_trend(days=90)
    
    analyzer = InsightsAnalyzer()
    report = analyzer.analyze_health(overview, charts)
    
    # Post to Slack
    webhook_url = os.environ.get("SLACK_WEBHOOK")
    if webhook_url:
        message = format_slack_message(report)
        resp = httpx.post(webhook_url, json=message)
        print(f"Slack response: {resp.status_code}")
    else:
        # Just print if no webhook configured
        print(json.dumps(format_slack_message(report), indent=2))


if __name__ == "__main__":
    main()
