"""Public board spatial model API for Richman."""

from .model import (
    Board,
    MoveResult,
    create,
    get_cell_type,
    get_property_template,
    get_range,
    move,
    total_cells,
)

__all__ = [
    "Board",
    "MoveResult",
    "create",
    "get_cell_type",
    "get_property_template",
    "get_range",
    "move",
    "total_cells",
]
