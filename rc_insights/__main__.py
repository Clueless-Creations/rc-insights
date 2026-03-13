"""Entry point for python -m rc_insights.

Routes to CLI by default, or MCP server with --mcp flag.
"""
import sys

if "--mcp" in sys.argv:
    sys.argv.remove("--mcp")
    from rc_insights.mcp_server import main
else:
    from rc_insights.cli import main

main()
