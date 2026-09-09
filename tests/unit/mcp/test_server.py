"""Unit tests for the lab telecom MCP server."""

from __future__ import annotations

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from eleven_demo.agents.tool_webhook import dispatch_convai_demo_tool
from eleven_demo.agents.tools import LookupTelecomAccountOutput
from eleven_demo.mcp.server import (
    SERVER_INSTRUCTIONS,
    SERVER_NAME,
    build_server,
    lookup_telecom_account_tool,
)


def _structured_payload(result: object) -> dict[str, object]:
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured
    if isinstance(result, dict):
        return result
    if isinstance(result, tuple) and result and isinstance(result[0], dict):
        return result[0]
    msg = f"unexpected call_tool result shape: {type(result)!r}"
    raise AssertionError(msg)


def test_lookup_accepts_formatted_cpf() -> None:
    out = lookup_telecom_account_tool("123.456.789-09")
    payload = out.model_dump(mode="json")
    assert payload["account_ref_masked"].endswith("8909")
    assert "plan_summary" in payload
    assert isinstance(out, LookupTelecomAccountOutput)


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
    output_schema = tool.output_schema
    assert output_schema is not None
    assert output_schema.get("additionalProperties") is False
    assert "account_ref_masked" in output_schema.get("properties", {})


async def test_call_tool_invalid_cpf_is_tool_error() -> None:
    server = build_server()
    with pytest.raises(ToolError, match="11 digits") as exc_info:
        await server.call_tool("lookup_telecom_account", {"cpf": "123"})
    message = str(exc_info.value)
    assert "Traceback" not in message
    assert "input_value" not in message


def test_lookup_matches_webhook_dispatch() -> None:
    cpf = "123.456.789-09"
    mcp_payload = lookup_telecom_account_tool(cpf).model_dump(mode="json")
    webhook_payload = dispatch_convai_demo_tool(
        {"tool_name": "lookup_telecom_account", "cpf": cpf},
    )
    assert mcp_payload == webhook_payload


async def test_call_tool_ignores_extra_keys() -> None:
    server = build_server()
    result = await server.call_tool(
        "lookup_telecom_account",
        {"cpf": "123.456.789-09", "foo": "bar"},
    )
    structured = _structured_payload(result)
    assert structured["account_ref_masked"].endswith("8909")


async def test_call_tool_null_cpf_is_tool_error() -> None:
    server = build_server()
    with pytest.raises(ToolError) as exc_info:
        await server.call_tool("lookup_telecom_account", {"cpf": None})
    assert "Traceback" not in str(exc_info.value)


async def test_call_tool_numeric_cpf_is_tool_error() -> None:
    server = build_server()
    with pytest.raises(ToolError) as exc_info:
        await server.call_tool("lookup_telecom_account", {"cpf": 12345678909})
    assert "Traceback" not in str(exc_info.value)
