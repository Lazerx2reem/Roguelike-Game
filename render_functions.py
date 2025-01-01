from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import color  # Assumes this module has color.bar_empty, color.bar_filled, color.bar_text, etc.

if TYPE_CHECKING:
    from tcod import Console


def render_bar(
    console: Console,
    current_value: int,
    maximum_value: int,
    total_width: int,
    *,
    x: int = 0,
    y: int = 45,
    title: str = "HP",
    dynamic_colors: bool = True,
    bar_bg_color=None,
    bar_fg_color=None,
    text_color=None,
) -> None:
    """
    Render a horizontal bar on the console to depict current vs. maximum values.

    :param console: The tcod Console where the bar should be drawn.
    :param current_value: The current value (e.g., current HP).
    :param maximum_value: The maximum value (e.g., max HP).
    :param total_width: The total width (in characters) of the bar.
    :param x: The left position (column) of the bar in the console.
    :param y: The vertical position (row) of the bar in the console.
    :param title: An optional label to display. Defaults to "HP".
    :param dynamic_colors: Whether to dynamically adjust the bar color based on the fraction of remaining value.
    :param bar_bg_color: Background color for the empty portion of the bar. (If None, uses color.bar_empty.)
    :param bar_fg_color: Fill color for the portion of the bar. (If None, uses color.bar_filled or a dynamic color.)
    :param text_color: Color for the text label. (If None, uses color.bar_text.)
    """

    if maximum_value <= 0:
        raise ValueError("Maximum value must be greater than 0.")
    if current_value < 0:
        current_value = 0
    if current_value > maximum_value:
        current_value = maximum_value

    # Default to color constants if none are provided
    if bar_bg_color is None:
        bar_bg_color = color.bar_empty
    if text_color is None:
        text_color = color.bar_text

    # Determine the fraction (0.0 to 1.0) of the bar that should be filled
    fraction = float(current_value) / maximum_value
    bar_width = int(fraction * total_width)

    # If we want dynamic coloration, we can pick from a few thresholds
    # Example logic: above 50% => green, 25%-50% => yellow, below 25% => red
    if dynamic_colors:
        if fraction < 0.25:
            used_fg = (191, 0, 0)  # red-ish
        elif fraction < 0.50:
            used_fg = (255, 191, 0)  # yellow-ish
        else:
            used_fg = (0, 191, 0)  # green-ish
    else:
        used_fg = color.bar_filled or (0, 191, 0)

    # If the user explicitly provided bar_fg_color, use that instead
    if bar_fg_color is not None:
        used_fg = bar_fg_color

    # Draw the "empty" part of the bar
    console.draw_rect(
        x=x,
        y=y,
        width=total_width,
        height=1,
        ch=1,   # A filler character; may also choose 0 or ' '
        bg=bar_bg_color,
    )

    # Draw the "filled" portion
    if bar_width > 0:
        console.draw_rect(
            x=x,
            y=y,
            width=bar_width,
            height=1,
            ch=1,
            bg=used_fg,
        )

    # Print the numeric info over the bar
    # e.g. "HP: 24/60"
    label = f"{title}: {current_value}/{maximum_value}"
    console.print(
        x=x + 1,
        y=y,
        string=label,
        fg=text_color,
    )
