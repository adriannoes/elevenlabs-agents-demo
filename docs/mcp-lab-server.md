# Lab MCP server (stdio)

A **local** Model Context Protocol server that exposes the same deterministic `lookup_telecom_account` mock the Telecom ElevenAgents webhook uses. It exists so you can attach a tool server from Claude Desktop, Cursor, or any MCP client without a public URL.

This is **not**:

- The [hosted ElevenLabs MCP](https://elevenlabs.io/docs/eleven-agents/operate/hosted-mcp) (`https://api.elevenlabs.io/v1/mcp`, OAuth, manage agents in your workspace).
- The archived [`elevenlabs/elevenlabs-mcp`](https://github.com/elevenlabs/elevenlabs-mcp) stdio server (archived 2026-08-20 in favor of hosted).
- A production CRM.

Field notes on why those three are easy to mix up: [Learning experience — MCP](../product/learning-experience.md#mcp-as-a-developer-surface).

## Run

Install the optional extra, then start the process:

```bash
uv sync --extra mcp
uv run python scripts/mcp_telecom.py
```

The process speaks MCP over **stdio**. Do not curl it. Configure your client with that command and `cwd` at the repo root (so `uv` finds `pyproject.toml`).

Example Claude Desktop snippet (paths will differ):

```json
{
  "mcpServers": {
    "eleven-demo-telecom": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/elevenlabs-agents-demo",
        "python",
        "scripts/mcp_telecom.py"
      ]
    }
  }
}
```

## Tool

`lookup_telecom_account`

| Input | Notes |
| --- | --- |
| `cpf` | 11 digits; separators allowed (`123.456.789-09`) |

Output is masked account ref, BRL balance, plan, support channel — synthetic, deterministic.

Unknown arguments are ignored by the MCP SDK; only `cpf` is validated. An invalid CPF returns an `is_error` result with a short message (digit count only; the raw value is not echoed).

Implementation: `src/eleven_demo/mcp/server.py` (`mcp` SDK v2 `MCPServer`, wraps `eleven_demo.agents.tools`).

## Tests

```bash
uv run pytest tests/unit/mcp -q
```

No live ElevenLabs calls.

## When to use hosted MCP instead

If you want Claude to **create or edit agents in your ElevenLabs workspace**, use the hosted server and OAuth. This lab process cannot do that; it only serves the mock tool.
