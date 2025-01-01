from __future__ import annotations

from typing import TYPE_CHECKING

import tcod
from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

from input_handlers import MainGameEventHandler
from render_functions import render_bar

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap
    from input_handlers import EventHandler


class Engine:
    """
    The main game engine that handles the player's interactions,
    updates the field of view, runs each actor's turn, and renders
    the game state to the screen.
    """

    game_map: GameMap

    def __init__(self, player: Actor) -> None:
        """
        Initialize the engine with a player actor.

        :param player: The player-controlled Actor entity.
        """
        self.event_handler: EventHandler = MainGameEventHandler(self)
        self.player = player

    def handle_enemy_turns(self) -> None:
        """
        Execute AI behavior for all entities that are not the player.
        """
        # Convert to a set to avoid double iteration on duplicates.
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                entity.ai.perform()

    def update_fov(self) -> None:
        """
        Recompute the visible area based on the player's position.
        Update both 'visible' and 'explored' tiles on the game map.
        """
        self.game_map.visible[:] = compute_fov(
            transparency_map=self.game_map.tiles["transparent"],
            xy=(self.player.x, self.player.y),
            radius=8,
        )
        # Mark all newly-visible tiles as explored.
        self.game_map.explored |= self.game_map.visible

    def render(self, console: Console, context: Context) -> None:
        """
        Render the entire game state to the given console, then display
        using the provided context.

        :param console: The console on which to render.
        :param context: The context responsible for presenting the console.
        """
        # First, draw the map with all its entities.
        self.game_map.render(console)

        # Now, draw a health bar near the top or bottom of the screen.
        # We choose y=45 here as an example, assuming a default terminal height of 50.
        # Adapt the position or style to match your game’s layout.
        render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            maximum_value=self.player.fighter.max_hp,
            total_width=20,
            x=1,
            y=45,
            title="HP",
            bar_color=(191, 0, 0),         # Red color for the filled portion
            bg_color=(75, 75, 75),         # Gray color for the background
        )

        # Optionally, label numeric HP over the bar (example to show text):
        console.print(
            x=1,
            y=46,
            string=f"HP: {self.player.fighter.hp}/{self.player.fighter.max_hp}",
            fg=(255, 255, 255),
        )

        # Present everything we just drew to the screen.
        context.present(console)
        # Clear the console for subsequent frames.
        console.clear()
