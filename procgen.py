from __future__ import annotations

import random
from typing import TYPE_CHECKING, Iterator, List, Optional, Tuple

import tcod

import entity_factories
from game_map import GameMap
import tile_types

if TYPE_CHECKING:
    from engine import Engine


class RectangularRoom:
    """
    A helper class representing a rectangular room on the dungeon grid.

    :param x: The top-left corner (column) of the room.
    :param y: The top-left corner (row) of the room.
    :param width: Room width in grid cells.
    :param height: Room height in grid cells.
    """

    __slots__ = ("x1", "y1", "x2", "y2")

    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        """
        Return the center cell of this rectangular room as (x, y).

        Useful for:
            - Player starting location
            - Spawning other critical items or features
        """
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """
        Return 2D array slices for the 'inner' area of this room.

        So the interior can be processed or 'dug out'. Excludes walls.

        Example usage:
            dungeon.tiles[new_room.inner] = tile_types.floor
        """
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    def intersects(self, other: RectangularRoom) -> bool:
        """
        Check if this RectangularRoom overlaps (intersects) with another.

        :param other: Another RectangularRoom instance
        :return: True if they overlap
        """
        return (
            self.x1 <= other.x2
            and self.x2 >= other.x1
            and self.y1 <= other.y2
            and self.y2 >= other.y1
        )


def place_entities(
    room: RectangularRoom,
    dungeon: GameMap,
    maximum_monsters: int,
    maximum_items: int,
    monster_chance: float = 0.8,
) -> None:
    """
    Spawn monster entities within the given room.

    :param room: The room within which to place the monsters.
    :param dungeon: The entire dungeon GameMap.
    :param maximum_monsters: The max number of monsters to spawn in this room.
    :param monster_chance: Probability that a spawned monster is one kind vs. another.
    """
    number_of_monsters = random.randint(0, maximum_monsters)
    number_of_items = random.randint(0, maximum_items)

    for _ in range(number_of_monsters):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        # Only place the monster if the cell is not already occupied:
        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            # 80% chance to spawn an orc vs. 20% chance for a troll (default)
            if random.random() < monster_chance:
                entity_factories.orc.spawn(dungeon, x, y)
            else:
                entity_factories.troll.spawn(dungeon, x, y)
    
    for i in range(number_of_items):
        x = random.randint(room.x1 + 1, room.x2 - 1)
        y = random.randint(room.y1 + 1, room.y2 - 1)

        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            entity_factories.health_potion.spawn(dungeon, x, y)



def tunnel_between(start: Tuple[int, int], end: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
    """
    Return an L-shaped tunnel between the given two points (Bresenham-based).

    First segment can be horizontal or vertical depending on a coin toss,
    then the second segment completes the path.

    :param start: (x, y) starting cell
    :param end: (x, y) ending cell
    :yield: (x, y) cells along the corridor path
    """
    x1, y1 = start
    x2, y2 = end

    if random.random() < 0.5:
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2

    # First leg of the L:
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)):
        yield x, y
    # Second leg of the L:
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)):
        yield x, y


def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    max_monsters_per_room: int,
    max_items_per_room: int,
    engine: Engine,
    *,
    random_tunnel: bool = True,
) -> GameMap:
    """
    Generate a brand-new, randomized dungeon map.

    :param max_rooms: The max number of rooms to attempt to place.
    :param room_min_size: The smallest possible room dimension.
    :param room_max_size: The largest possible room dimension.
    :param map_width: The total width of the dungeon map in tiles.
    :param map_height: The total height of the dungeon map in tiles.
    :param max_monsters_per_room: The maximum number of monsters to spawn in each room.
    :param engine: The engine, providing global context (player actor, etc).
    :param random_tunnel: If True, picks the corridor path direction randomly. Otherwise could do a single corridor style.
    :return: The fully built GameMap instance, with rooms/corridors/monsters placed.
    """
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []

    for _ in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        new_room = RectangularRoom(x, y, room_width, room_height)

        # check for collisions with existing rooms
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # skip if intersecting

        # Carve out the floor for the new room
        dungeon.tiles[new_room.inner] = tile_types.floor

        if not rooms:
            # This is the first room, place the player here
            player.place(*new_room.center, dungeon)
        else:
            # Connect the last room to this one with corridors
            for x_cur, y_cur in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x_cur, y_cur] = tile_types.floor

        # Spawn some monsters
        place_entities(new_room, dungeon, max_monsters_per_room, max_items_per_room)
        rooms.append(new_room)

    # Optionally, could place additional features here

    return dungeon
