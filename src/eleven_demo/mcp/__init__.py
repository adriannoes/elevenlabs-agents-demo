"""Local MCP server for this lab (stdio). Not the ElevenLabs hosted MCP.

Uses the MCP Python SDK v2 ``MCPServer`` (formerly FastMCP).
"""

from eleven_demo.mcp.server import build_server, lookup_telecom_account_tool

__all__ = ["build_server", "lookup_telecom_account_tool"]
