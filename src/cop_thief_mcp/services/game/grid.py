"""Grid geometry: roles, actions, positions, and boundary checks."""

from dataclasses import dataclass
from enum import Enum


class Role(Enum):
    COP = "cop"
    THIEF = "thief"


class Action(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    PASS = "pass"
    PLACE_BARRIER = "place_barrier"


MOVE_ACTIONS = (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT)

_DELTAS = {
    Action.UP: (-1, 0),
    Action.DOWN: (1, 0),
    Action.LEFT: (0, -1),
    Action.RIGHT: (0, 1),
}


@dataclass(frozen=True)
class Position:
    row: int
    col: int

    def moved(self, action: Action) -> "Position":
        """Return the position reached by applying a movement action (PASS/PLACE_BARRIER stay put)."""
        d_row, d_col = _DELTAS.get(action, (0, 0))
        return Position(self.row + d_row, self.col + d_col)


@dataclass(frozen=True)
class Grid:
    rows: int
    cols: int

    def in_bounds(self, pos: Position) -> bool:
        return 0 <= pos.row < self.rows and 0 <= pos.col < self.cols
