from __future__ import annotations

import numpy as np
from typing import Tuple

# A structured NumPy dtype to store tile graphics
graphic_dt = np.dtype(
    [
        ("ch", np.int32),       # The Unicode or ASCII character to represent the tile
        ("fg", "3B"),           # Foreground color (R, G, B)
        ("bg", "3B"),           # Background color (R, G, B)
    ]
)

# A structured NumPy dtype to store tile properties
tile_dt = np.dtype(
    [
        ("walkable", np.bool_),    # True if tiles can be walked over
        ("transparent", np.bool_), # True if tiles do not block FOV
        ("dark", graphic_dt),      # Appearance when not in the player's FOV
        ("light", graphic_dt),     # Appearance when in the player's FOV
    ]
)

def new_tile(
    *,
    walkable: bool,
    transparent: bool,
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    """
    Define and return a new tile with the specified properties.

    :param walkable: Whether the tile can be walked on (no collisions).
    :param transparent: Whether the tile blocks field-of-view.
    :param dark: A 3-tuple describing (char, fg_color, bg_color) in unlit/dark conditions.
    :param light: A 3-tuple describing (char, fg_color, bg_color) in lit/in-FOV conditions.

    :return: A structured NumPy array of dtype=tile_dt representing this tile.
    """
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)

# SHROUD is how we represent unexplored tiles
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

# Define a floor tile
floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(" "), (255, 255, 255), (50, 50, 150)),
    light=(ord(" "), (255, 255, 255), (200, 180, 50)),
)

# Define a wall tile
wall = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord(" "), (255, 255, 255), (0, 0, 100)),
    light=(ord(" "), (255, 255, 255), (130, 110, 50)),
)
