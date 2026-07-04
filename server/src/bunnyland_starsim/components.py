"""Components contributed by the starsim pack.

All state is immutable (frozen pydantic-dataclasses subclassing :class:`relics.Component`);
handlers and the night-sky consequence swap whole values with
``replace_component(entity, replace(component, ...))``.

- :class:`SkyComponent` is a **singleton** stored on the world clock entity. The
  :class:`~bunnyland_starsim.sky.NightSkyConsequence` derives it every tick from the clock
  (time of day, season, weather) so the visible sky is entirely calendar-driven.
- :class:`TelescopeComponent` sits on a held item and deepens a stargaze.
- :class:`ConstellationLogComponent` records which constellations a character has charted.
- :class:`WishLogComponent` counts wishes made during celestial events.
"""

from __future__ import annotations

from pydantic.dataclasses import dataclass
from relics import Component


@dataclass(frozen=True)
class SkyComponent(Component):
    """Tonight's sky, derived from the calendar (a singleton on the clock entity).

    ``stars_out`` is the *global* condition (it is night and the sky is clear); whether a
    given character can actually see the stars additionally requires an outdoor room, which
    is checked at the point of use.
    """

    day: int = 1
    season: str = "spring"
    phase: str = "night"
    condition: str = "clear"
    stars_out: bool = True
    constellations: tuple[str, ...] = ()
    event: str = ""


@dataclass(frozen=True)
class TelescopeComponent(Component):
    """A held optical aid. Higher ``power`` deepens a stargaze and its wonder."""

    power: float = 1.0


@dataclass(frozen=True)
class ConstellationLogComponent(Component):
    """A character's record of charted constellations (sorted, de-duplicated)."""

    identified: tuple[str, ...] = ()


@dataclass(frozen=True)
class WishLogComponent(Component):
    """A character's tally of wishes made under a celestial event."""

    wishes: int = 0
    last_event: str = ""


__all__ = [
    "ConstellationLogComponent",
    "SkyComponent",
    "TelescopeComponent",
    "WishLogComponent",
]
