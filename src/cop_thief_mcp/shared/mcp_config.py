"""Loads Cop/Thief MCP server host+port from config/mcp_servers.json. No hard-coded ports elsewhere."""

from dataclasses import dataclass
from pathlib import Path

from cop_thief_mcp.shared.constants import PROJECT_ROOT
from cop_thief_mcp.shared.json_loader import read_json

DEFAULT_MCP_SERVERS_CONFIG_PATH = PROJECT_ROOT / "config" / "mcp_servers.json"


@dataclass(frozen=True)
class ServerEndpoint:
    host: str
    port: int


@dataclass(frozen=True)
class McpServersConfig:
    version: str
    cop_server: ServerEndpoint
    thief_server: ServerEndpoint


def load_mcp_servers_config(path: Path | None = None) -> McpServersConfig:
    """Read and validate the Cop/Thief MCP server endpoints from a JSON file."""
    config_path = path or DEFAULT_MCP_SERVERS_CONFIG_PATH
    raw = read_json(config_path)

    return McpServersConfig(
        version=raw["version"],
        cop_server=ServerEndpoint(**raw["cop_server"]),
        thief_server=ServerEndpoint(**raw["thief_server"]),
    )
