from __future__ import annotations

from typing import TYPE_CHECKING

from components.base_component import BaseComponent
from render_order import RenderOrder
from input_handlers import GameOverEventHandler

if TYPE_CHECKING:
    from entity import Actor
    from engine import Engine  # Hypothetical import; if you need direct reference to Engine

class Fighter(BaseComponent):
    """
    Represents combat-relevant statistics and behavior for an Actor.

    This component stores the fighter's hit points, defense, and power,
    along with logic for dying when HP reaches zero. Dying triggers
    a transition to a game-over event handler if the entity is the player.
    """

    entity: Actor

    def __init__(self, hp: int, defense: int, power: int) -> None:
        """
        Initialize the Fighter component with health, defense, and power.

        :param hp: The maximum (and initial) hit points for the Actor.
        :param defense: How much incoming damage is reduced.
        :param power: How much damage the Actor can inflict.
        """
        super().__init__()  # If BaseComponent has an __init__
        self.max_hp: int = hp
        self._hp: int = hp
        self.defense: int = defense
        self.power: int = power

    @property
    def hp(self) -> int:
        """
        The current hit points. Will never exceed max_hp or go below 0.
        """
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        """
        Sets the current HP, clamped between 0 and max_hp.
        If HP hits 0, the entity will die if it has an AI.
        """
        self._hp = max(0, min(value, self.max_hp))
        if self._hp == 0 and self.entity.ai:
            self.die()

    def die(self) -> None:
        """
        Handle the death of the associated Actor.

        Transitions the player to a GameOverEventHandler if it's the player's Fighter.
        Otherwise changes the entity to a 'corpse' state.
        """
        if self.engine.player is self.entity:
            # The player has died
            death_message: str = "You died!"
            # Switch event handler to game-over state
            self.engine.event_handler = GameOverEventHandler(self.engine)
        else:
            # Some other Actor has died
            death_message = f"{self.entity.name} is dead!"

        # Convert the entity to a corpse
        self.entity.char = "%"
        self.entity.color = (191, 0, 0)
        self.entity.blocks_movement = False
        self.entity.ai = None
        self.entity.name = f"Remains of {self.entity.name}"
        self.entity.render_order = RenderOrder.CORPSE

        print(death_message)
