"""Unit tests for the lab telecom MCP server."""

from __future__ import annotations

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from eleven_demo.mcp.server import (
    SERVER_INSTRUCTIONS,
    SERVER_NAME,
    build_server,
    lookup_telecom_account_tool,
)


def test_lookup_accepts_formatted_cpf() -> None:
    out = lookup_telecom_account_tool("123.456.789-09")
    assert out["account_ref_masked"].endswith("8909")
    assert "plan_summary" in out


def test_lookup_rejects_short_cpf() -> None:
    with pytest.raises(ToolError, match="11 digits") as exc_info:
        lookup_telecom_account_tool("123")
    assert "Traceback" not in str(exc_info.value)
    assert "123" not in str(exc_info.value)


def test_lookup_is_deterministic() -> None:
    a = lookup_telecom_account_tool("11144477735")
    b = lookup_telecom_account_tool("11144477735")
    assert a == b


def test_build_server_identity() -> None:
    server = build_server()
    assert server.name == SERVER_NAME
    assert "hosted server" in SERVER_INSTRUCTIONS
    assert "eleven-demo" in SERVER_INSTRUCTIONS


def test_build_server_version_not_empty() -> None:
    server = build_server()
    assert server.version
    assert server.version != ""


async def test_list_tools_schema() -> None:
    tools = await build_server().list_tools()
    assert len(tools) == 1
    tool = tools[0]
    assert tool.name == "lookup_telecom_account"
    schema = tool.input_schema
    assert schema["required"] == ["cpf"]
    description = schema["properties"]["cpf"]["description"]
    assert "11 digits" in description


async def test_call_tool_invalid_cpf_is_tool_error() -> None:
    server = build_server()
    with pytest.raises(ToolError, match="11 digits") as exc_info:
        await server.call_tool("lookup_telecom_account", {"cpf": "123"})
    message = str(exc_info.value)
    assert "Traceback" not in message
    assert "input_value" not in message
