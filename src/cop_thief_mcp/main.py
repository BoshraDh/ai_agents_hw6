"""CLI entry point. Stage 1 only exercises the pure game engine; MCP servers land in later stages."""

from cop_thief_mcp.shared.config import load_config


def main() -> None:
    config = load_config()
    print(f"cop-thief-mcp v{config.version} — engine config loaded ({config.grid_rows}x{config.grid_cols} grid)")


if __name__ == "__main__":
    main()
