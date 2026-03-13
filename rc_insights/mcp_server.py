"""MCP server for rc-insights.

Exposes rc-insights as MCP tools so any agent runtime can discover and use it.
Implements the Model Context Protocol stdio transport.

Usage:
    python -m rc_insights.mcp_server

Or add to your MCP config:
    {
        "mcpServers": {
            "rc-insights": {
                "command": "python",
                "args": ["-m", "rc_insights.mcp_server"],
                "env": {"RC_API_KEY": "sk_..."}
            }
        }
    }
"""

import json
import sys
import os
from typing import Any

from rc_insights.client import ChartsClient, ChartName
from rc_insights.analyzer import InsightsAnalyzer, ToolResult
from rc_insights.report import ReportGenerator


def _json_line(obj: dict):
    """Write a JSON-RPC message to stdout."""
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _error_response(id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}}


def _success_response(id: Any, result: Any) -> dict:
    return {"jsonrpc": "2.0", "id": id, "result": result}


# ── Tool Definitions ──────────────────────────────────────────

TOOLS = [
    {
        "name": "rc_list_charts",
        "description": "Discover all available chart types from the RevenueCat Charts API. Call this first to know what data is available.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "rc_get_overview",
        "description": "Get current overview metrics: MRR, active subscriptions, active trials, revenue, new customers.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "rc_get_chart",
        "description": "Query a specific chart metric over a date range. Use rc_list_charts first to discover available chart names.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chart_name": {
                    "type": "string",
                    "description": "Chart name (e.g., 'mrr', 'churn', 'actives'). Use rc_list_charts to discover valid names.",
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format. Defaults to 30 days ago.",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format. Defaults to today.",
                },
                "resolution": {
                    "type": "string",
                    "enum": ["day", "week", "month"],
                    "description": "Time granularity. Defaults to 'day'.",
                },
            },
            "required": ["chart_name"],
        },
    },
    {
        "name": "rc_analyze_health",
        "description": "Run a complete subscription health analysis. Returns a health score (0-100), prioritized insights with severity levels, and actionable recommendations. This pulls multiple charts and analyzes them together.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to analyze. Default 30.",
                    "default": 30,
                },
                "mrr_growth_threshold": {
                    "type": "number",
                    "description": "MRR growth % to count as positive signal. Default 10.",
                },
                "churn_critical": {
                    "type": "number",
                    "description": "Churn % to flag as critical. Default 10.",
                },
                "anomaly_threshold": {
                    "type": "number",
                    "description": "Standard deviations for anomaly detection. Default 2.0.",
                },
            },
        },
    },
    {
        "name": "rc_calc_trend",
        "description": "Calculate trend direction and magnitude for a list of numeric values. Returns percentage change and recent average. Use this as a building block for custom analysis.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of numeric values in chronological order.",
                },
                "window": {
                    "type": "integer",
                    "description": "Rolling window size for comparison. Default 7.",
                    "default": 7,
                },
            },
            "required": ["values"],
        },
    },
    {
        "name": "rc_detect_anomalies",
        "description": "Find anomalous data points in a series using z-score detection. Returns indices, values, and direction (spike/drop) of anomalies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "values": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "List of numeric values.",
                },
                "threshold": {
                    "type": "number",
                    "description": "Standard deviations from mean to flag as anomaly. Default 2.0.",
                    "default": 2.0,
                },
            },
            "required": ["values"],
        },
    },
    {
        "name": "rc_generate_report",
        "description": "Generate a health report in HTML, Markdown, and/or JSON format. Runs a full health analysis and saves the results to files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Days to analyze. Default 30.",
                    "default": 30,
                },
                "formats": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["html", "md", "json"]},
                    "description": "Output formats. Default ['html', 'md', 'json'].",
                },
                "output_dir": {
                    "type": "string",
                    "description": "Directory to save reports. Default './rc-report'.",
                    "default": "./rc-report",
                },
            },
        },
    },
]


# ── Tool Handlers ─────────────────────────────────────────────

_client = None


def _get_client() -> ChartsClient:
    global _client
    if _client is None:
        _client = ChartsClient()
        _client.discover_project_id()
    return _client


def handle_rc_list_charts(params: dict) -> dict:
    client = _get_client()
    charts = client.list_available_charts()
    return {"charts": charts, "count": len(charts)}


def handle_rc_get_overview(params: dict) -> dict:
    client = _get_client()
    overview = client.get_overview()
    metrics = {}
    for m in overview.metrics:
        metrics[m.id] = {"name": m.name, "value": m.value, "unit": m.unit}
    return {"metrics": metrics}


def handle_rc_get_chart(params: dict) -> dict:
    client = _get_client()
    chart = client.get_chart(
        chart_name=params["chart_name"],
        start_date=params.get("start_date"),
        end_date=params.get("end_date"),
        resolution=params.get("resolution", "day"),
    )
    return {
        "chart_name": chart.chart_name,
        "display_name": chart.display_name,
        "description": chart.description,
        "resolution": chart.resolution,
        "measures": [{"name": m.display_name, "unit": m.unit} for m in chart.measures],
        "data_points": len(chart.data_points),
        "primary_values": chart.primary_values[:30],  # Limit for context window
        "primary_dates": chart.primary_dates[:30],
        "averages": chart.averages(),
        "summary": chart.summary,
    }


def handle_rc_analyze_health(params: dict) -> dict:
    client = _get_client()
    days = params.get("days", 30)

    overview = client.get_overview()
    charts = client.get_health_charts(days=days)

    kwargs = {}
    if "mrr_growth_threshold" in params:
        kwargs["mrr_growth_threshold"] = params["mrr_growth_threshold"]
    if "churn_critical" in params:
        kwargs["churn_critical"] = params["churn_critical"]
    if "anomaly_threshold" in params:
        kwargs["anomaly_std_threshold"] = params["anomaly_threshold"]

    analyzer = InsightsAnalyzer(**kwargs)
    report = analyzer.analyze_health(overview, charts)

    return report.to_dict()


def handle_rc_calc_trend(params: dict) -> dict:
    values = params["values"]
    window = params.get("window", 7)
    change_pct, recent_avg = InsightsAnalyzer.calc_trend(values, window)
    return {
        "change_percent": round(change_pct, 2),
        "recent_average": round(recent_avg, 2),
        "direction": "up" if change_pct > 0 else "down" if change_pct < 0 else "flat",
    }


def handle_rc_detect_anomalies(params: dict) -> dict:
    values = params["values"]
    threshold = params.get("threshold", 2.0)
    anomalies = InsightsAnalyzer.detect_anomalies(values, threshold)
    return {
        "anomalies": [
            {"index": idx, "value": round(val, 2), "direction": direction}
            for idx, val, direction in anomalies
        ],
        "count": len(anomalies),
    }


def handle_rc_generate_report(params: dict) -> dict:
    client = _get_client()
    days = params.get("days", 30)
    formats = params.get("formats", ["html", "md", "json"])
    output_dir = params.get("output_dir", "./rc-report")

    overview = client.get_overview()
    charts = client.get_health_charts(days=days)

    analyzer = InsightsAnalyzer()
    report = analyzer.analyze_health(overview, charts)

    generator = ReportGenerator()
    saved = generator.save(report, output_dir=output_dir, formats=formats)

    return {
        "saved_files": saved,
        "health_score": report.health_score.score,
        "grade": report.health_score.grade,
    }


HANDLERS = {
    "rc_list_charts": handle_rc_list_charts,
    "rc_get_overview": handle_rc_get_overview,
    "rc_get_chart": handle_rc_get_chart,
    "rc_analyze_health": handle_rc_analyze_health,
    "rc_calc_trend": handle_rc_calc_trend,
    "rc_detect_anomalies": handle_rc_detect_anomalies,
    "rc_generate_report": handle_rc_generate_report,
}


# ── MCP Protocol Handler ──────────────────────────────────────

def handle_request(request: dict) -> dict:
    """Handle a JSON-RPC request."""
    method = request.get("method", "")
    id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return _success_response(id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "rc-insights", "version": "0.2.0"},
        })

    elif method == "notifications/initialized":
        return None  # No response needed for notifications

    elif method == "tools/list":
        return _success_response(id, {"tools": TOOLS})

    elif method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})

        handler = HANDLERS.get(tool_name)
        if not handler:
            return _error_response(id, -32601, f"Unknown tool: {tool_name}")

        try:
            result = handler(tool_args)
            return _success_response(id, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2, default=str)}],
                "isError": False,
            })
        except Exception as e:
            return _success_response(id, {
                "content": [{"type": "text", "text": json.dumps({"error": str(e)}, indent=2)}],
                "isError": True,
            })

    elif method == "ping":
        return _success_response(id, {})

    else:
        return _error_response(id, -32601, f"Method not found: {method}")


def main():
    """Run the MCP server on stdio."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
            if response is not None:
                _json_line(response)
        except json.JSONDecodeError:
            _json_line(_error_response(None, -32700, "Parse error"))
        except Exception as e:
            _json_line(_error_response(None, -32603, f"Internal error: {e}"))


if __name__ == "__main__":
    main()
