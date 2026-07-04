"""Domain events emitted by the starsim mechanics."""

from __future__ import annotations

from bunnyland.core.events import DomainEvent


class StargazedEvent(DomainEvent):
    """A character looked up and studied the night sky."""

    phase: str = "night"
    constellation: str = ""


class ConstellationIdentifiedEvent(DomainEvent):
    """A character charted a constellation for the first time."""

    constellation: str


class WishMadeEvent(DomainEvent):
    """A character made a wish during a celestial event."""

    celestial_event: str


class SkyChangedEvent(DomainEvent):
    """The celestial event overhead began or ended."""

    celestial_event: str
    phase: str = "night"


__all__ = [
    "ConstellationIdentifiedEvent",
    "SkyChangedEvent",
    "StargazedEvent",
    "WishMadeEvent",
]
