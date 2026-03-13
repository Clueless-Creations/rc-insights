"""Report generators — transform analysis into publishable formats.

Outputs: HTML dashboard, Markdown report, JSON (for agent pipelines).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from rc_insights.analyzer import AnalysisReport, Severity


class ReportGenerator:
    """Generate reports from analysis results in multiple formats."""

    def to_json(self, report: AnalysisReport, pretty: bool = True) -> str:
        """Generate JSON report — ideal for agent consumption."""
        indent = 2 if pretty else None
        return json.dumps(report.to_dict(), indent=indent, default=str)

    def to_markdown(self, report: AnalysisReport) -> str:
        """Generate a Markdown report — ideal for Notion, GitHub, Slack."""
        lines = []
        lines.append("# RevenueCat Subscription Health Report")
        lines.append("")
        lines.append(f"*Generated: {report.generated_at}*")
        lines.append("")

        # Health score
        hs = report.health_score
        lines.append(f"## Health Score: {hs.score}/100 — Grade {hs.grade}")
        lines.append("")
        lines.append(hs.summary)
        lines.append("")

        # Summary
        if report.summary:
            lines.append("## Overview")
            lines.append("")
            lines.append(report.summary)
            lines.append("")

        # Critical issues first
        if report.critical_insights:
            lines.append("## 🚨 Critical Issues")
            lines.append("")
            for insight in report.critical_insights:
                lines.append(f"### {insight.title}")
                lines.append(f"{insight.description}")
                if insight.recommendation:
                    lines.append(f"**Recommendation:** {insight.recommendation}")
                lines.append("")

        # Warnings
        if report.warnings:
            lines.append("## ⚠️ Warnings")
            lines.append("")
            for insight in report.warnings:
                lines.append(f"### {insight.title}")
                lines.append(f"{insight.description}")
                if insight.recommendation:
                    lines.append(f"**Recommendation:** {insight.recommendation}")
                lines.append("")

        # Positive signals
        if report.positive_signals:
            lines.append("## ✅ Positive Signals")
            lines.append("")
            for insight in report.positive_signals:
                lines.append(f"### {insight.title}")
                lines.append(f"{insight.description}")
                lines.append("")

        return "\n".join(lines)

    def to_html(self, report: AnalysisReport) -> str:
        """Generate a self-contained HTML dashboard report."""
        severity_colors = {
            "critical": "#dc2626",
            "warning": "#f59e0b",
            "positive": "#10b981",
            "info": "#6b7280",
        }

        grade_colors = {
            "A": "#10b981",
            "B": "#34d399",
            "C": "#f59e0b",
            "D": "#f97316",
            "F": "#dc2626",
        }

        hs = report.health_score
        grade_color = grade_colors.get(hs.grade, "#6b7280")

        insights_html = ""
        for insight in report.insights:
            color = severity_colors.get(insight.severity.value, "#6b7280")
            rec_html = f'<p class="recommendation"><strong>→</strong> {insight.recommendation}</p>' if insight.recommendation else ""
            change_html = ""
            if insight.change_pct is not None:
                arrow = "↑" if insight.change_pct > 0 else "↓"
                change_html = f'<span class="change" style="color: {color}">{arrow} {abs(insight.change_pct):.1f}%</span>'

            insights_html += f"""
            <div class="insight-card" style="border-left: 4px solid {color}">
                <div class="insight-header">
                    <h3>{insight.title}</h3>
                    {change_html}
                </div>
                <p>{insight.description}</p>
                {rec_html}
            </div>
            """

        overview_html = f"<p>{report.summary}</p>" if report.summary else ""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RevenueCat Subscription Health Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 2rem;
            max-width: 900px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 1.75rem;
            margin-bottom: 0.5rem;
            color: #f8fafc;
        }}
        .subtitle {{
            color: #94a3b8;
            font-size: 0.875rem;
            margin-bottom: 2rem;
        }}
        .health-score {{
            background: #1e293b;
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            margin-bottom: 2rem;
        }}
        .score-number {{
            font-size: 4rem;
            font-weight: 800;
            color: {grade_color};
        }}
        .score-grade {{
            font-size: 1.25rem;
            color: {grade_color};
            margin-bottom: 0.5rem;
        }}
        .score-summary {{
            color: #94a3b8;
            font-size: 0.9rem;
        }}
        .overview {{
            background: #1e293b;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            color: #cbd5e1;
        }}
        .insights-section {{
            margin-bottom: 2rem;
        }}
        .insights-section h2 {{
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: #f8fafc;
        }}
        .insight-card {{
            background: #1e293b;
            border-radius: 8px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        }}
        .insight-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }}
        .insight-header h3 {{
            font-size: 1rem;
            color: #f8fafc;
        }}
        .change {{
            font-weight: 600;
            font-size: 0.9rem;
        }}
        .insight-card p {{
            color: #94a3b8;
            font-size: 0.875rem;
            line-height: 1.5;
        }}
        .recommendation {{
            margin-top: 0.75rem;
            color: #cbd5e1 !important;
            font-style: italic;
        }}
        .footer {{
            text-align: center;
            color: #475569;
            font-size: 0.75rem;
            margin-top: 3rem;
            padding-top: 1rem;
            border-top: 1px solid #1e293b;
        }}
        .footer a {{ color: #6366f1; text-decoration: none; }}
    </style>
</head>
<body>
    <h1>Subscription Health Report</h1>
    <p class="subtitle">Generated {report.generated_at} by rc-insights</p>

    <div class="health-score">
        <div class="score-number">{hs.score}</div>
        <div class="score-grade">Grade {hs.grade}</div>
        <div class="score-summary">{hs.summary}</div>
    </div>

    <div class="overview">
        {overview_html}
    </div>

    <div class="insights-section">
        <h2>Insights ({len(report.insights)})</h2>
        {insights_html}
    </div>

    <div class="footer">
        Powered by <a href="https://github.com/katire-agent/rc-insights">rc-insights</a>
        · Built for the <a href="https://www.revenuecat.com/docs/dashboard-and-metrics/charts">RevenueCat Charts API</a>
        · By Katire 🤖
    </div>
</body>
</html>"""

    def save(
        self,
        report: AnalysisReport,
        output_dir: str = ".",
        formats: Optional[list[str]] = None,
    ) -> list[str]:
        """Save report in all requested formats. Returns list of file paths."""
        formats = formats or ["html", "md", "json"]
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        saved = []

        if "html" in formats:
            path = output / "health-report.html"
            path.write_text(self.to_html(report))
            saved.append(str(path))

        if "md" in formats:
            path = output / "health-report.md"
            path.write_text(self.to_markdown(report))
            saved.append(str(path))

        if "json" in formats:
            path = output / "health-report.json"
            path.write_text(self.to_json(report))
            saved.append(str(path))

        return saved
