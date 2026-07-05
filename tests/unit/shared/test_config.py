from cop_thief_mcp.shared.config import load_config
from cop_thief_mcp.shared.constants import DEFAULT_CONFIG_PATH


def test_load_config_reads_default_setup_json():
    config = load_config(DEFAULT_CONFIG_PATH)

    assert config.version == "1.00"
    assert (config.grid_rows, config.grid_cols) == (5, 5)
    assert config.max_moves == 25
    assert config.num_games == 6
    assert config.max_barriers == 5
    assert config.scoring.cop_win_cop == 20
    assert config.scoring.cop_win_thief == 5
    assert config.scoring.thief_win_cop == 5
    assert config.scoring.thief_win_thief == 10
