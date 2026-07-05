from cop_thief_mcp.shared.mcp_config import load_mcp_servers_config


def test_load_mcp_servers_config_reads_default_file():
    config = load_mcp_servers_config()

    assert config.version == "1.00"
    assert config.cop_server.host == "127.0.0.1"
    assert config.cop_server.port == 8001
    assert config.thief_server.host == "127.0.0.1"
    assert config.thief_server.port == 8002


def test_cop_and_thief_use_different_ports():
    config = load_mcp_servers_config()

    assert config.cop_server.port != config.thief_server.port
