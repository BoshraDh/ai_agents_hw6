import random

from cop_thief_mcp.services.decision.q_learning import QTable
from cop_thief_mcp.services.decision.q_learning_training import run_training_episode, train_q_tables
from cop_thief_mcp.services.game.grid import Grid, Position


def test_run_training_episode_updates_both_tables():
    grid = Grid(rows=3, cols=3)
    cop_table = QTable()
    thief_table = QTable()
    rng = random.Random(1)

    run_training_episode(
        grid, max_moves=10, max_barriers=2, cop_table=cop_table, thief_table=thief_table,
        alpha=0.1, gamma=0.9, epsilon=0.5, rng=rng,
        cop_start=Position(0, 0), thief_start=Position(2, 2),
    )

    assert len(cop_table.values) > 0
    assert len(thief_table.values) > 0


def test_train_q_tables_is_deterministic_given_the_same_seed():
    grid = Grid(rows=3, cols=3)

    cop_a, thief_a = train_q_tables(grid, max_moves=10, max_barriers=2, episodes=25, seed=7)
    cop_b, thief_b = train_q_tables(grid, max_moves=10, max_barriers=2, episodes=25, seed=7)

    assert cop_a.values == cop_b.values
    assert thief_a.values == thief_b.values
    assert len(cop_a.values) > 0
