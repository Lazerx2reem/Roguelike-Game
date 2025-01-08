from __future__ import annotations

import random
from typing import TYPE_CHECKING, Iterator, List, Optional, Tuple

import tcod

import entity_factories
from game_map import GameMap
import tile_types

if TYPE_CHECKING:
    from engine import Engine

max_items_by_floor = [
    (1, 1),
    (4, 2),
 ]

max_monsters_by_floor = [
    (1, 2),
    (4, 3),
    (6, 5),
]

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
            item_chance = random.random()

            if item_chance < 0.7:
                entity_factories.health_potion.spawn(dungeon, x, y)
            elif item_chance < 0.8:
                entity_factories.fireball_scroll.spawn(dungeon, x, y)
            elif item_chance < 0.9:
                entity_factories.confusion_scroll.spawn(dungeon, x, y)
            else:
                entity_factories.lightning_scroll.spawn(dungeon, x, y)



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
) -> GameMap:
    """Generate a new dungeon map."""
    player = engine.player
    dungeon = GameMap(engine, map_width, map_height, entities=[player])

    rooms: List[RectangularRoom] = []

    center_of_last_room = (0, 0)

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # "RectangularRoom" class makes rectangles easier to work with
        new_room = RectangularRoom(x, y, room_width, room_height)

        # Run through the other rooms and see if they intersect with this one.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # This room intersects, so go to the next attempt.
        # If there are no intersections then the room is valid.

        # Dig out this rooms inner area.
        dungeon.tiles[new_room.inner] = tile_types.floor

        if len(rooms) == 0:
            # The first room, where the player starts.
            player.place(*new_room.center, dungeon)
        else:  # All rooms after the first.
            # Dig out a tunnel between this room and the previous one.
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

            center_of_last_room = new_room.center

        place_entities(new_room, dungeon, max_monsters_per_room, max_items_per_room)

        dungeon.tiles[center_of_last_room] = tile_types.down_stairs
        dungeon.downstairs_location = center_of_last_room

        # Finally, append the new room to the list.
        rooms.append(new_room)

    return dungeon