"""Stdio MCP server wrapping the deterministic telecom account mock.

This is a *lab* server so an MCP client (Claude, Cursor, or a test harness) can
call the same ``lookup_telecom_account`` mock the ElevenAgents webhook uses.
It is not a substitute for the [hosted ElevenLabs MCP](https://elevenlabs.io/docs/eleven-agents/operate/hosted-mcp).

The MCP SDK ignores unknown extra arguments; only ``cpf`` is validated. The
Pydantic model's ``extra="forbid"`` is not enforced at this boundary because the
tool is a single string parameter, not the nested input model.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field, ValidationError

from eleven_demo.agents.tools import (
    LookupTelecomAccountInput,
    mock_lookup_telecom_account,
    normalize_cpf_digits,
)

SERVER_NAME = "eleven-demo-telecom"
SERVER_INSTRUCTIONS = (
    "Lab MCP server for the eleven-demo repository. Exposes a deterministic "
    "mock of lookup_telecom_account (fictional Brazilian telecom SAC). "
    "Not an official ElevenLabs MCP server. For workspace agent management, "
    "use the hosted server at https://api.elevenlabs.io/v1/mcp."
)

_CPF_DESCRIPTION = "Brazilian CPF, 11 digits; separators allowed, e.g. 123.456.789-09"


def _package_version() -> str:
    try:
        return version("eleven-demo")
    except PackageNotFoundError:
        return "0.0.0+local"


def lookup_telecom_account_tool(
    cpf: Annotated[str, Field(description=_CPF_DESCRIPTION)],
) -> dict[str, Any]:
    """Look up a fictional telecom account by CPF (11 digits, separators allowed)."""

    try:
        inp = LookupTelecomAccountInput.model_validate({"cpf": cpf})
    except ValidationError:
        digit_count = len(normalize_cpf_digits(cpf))
        msg = (
            "cpf must contain exactly 11 digits (separators allowed); "
            f"got a value with {digit_count} digits"
        )
        raise ToolError(msg) from None
    return mock_lookup_telecom_account(inp).model_dump(mode="json")


def build_server() -> MCPServer:
    """Return a configured MCP server (stdio by default)."""

    mcp = MCPServer(
        SERVER_NAME,
        instructions=SERVER_INSTRUCTIONS,
        version=_package_version(),
    )
    mcp.tool(
        name="lookup_telecom_account",
        description=(
            "Look up a fictional mobile/fixed-line account after an 11-digit CPF. "
            "Returns masked account ref, balance in BRL, plan, and support channel. "
            "Synthetic data only."
        ),
    )(lookup_telecom_account_tool)
    return mcp


def main() -> None:
    """Run the server over stdio (MCP client child process)."""

    build_server().run(transport="stdio")
