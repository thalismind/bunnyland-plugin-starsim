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


class BodyTrackedEvent(DomainEvent):
    """A character charted a planet or comet tonight."""

    body: str
    kind: str = "planet"
    sightings: int = 1
    instrument: str = "naked eye"


class BodySightedEvent(DomainEvent):
    """A character sighted a planet or comet for the very first time."""

    body: str
    kind: str = "planet"


class CelestialEventBeganEvent(DomainEvent):
    """A world-wide celestial spectacle (a meteor shower or comet) began overhead.

    Published for any pack that wants to react to the sky — e.g. a festival throwing a
    meteor-shower spectacle. It carries the storyteller ``incident_id`` the sky opened so a
    consumer can tie its reaction to the shared incident.
    """

    celestial_event: str
    incident_id: str
    spectacle: str = ""


__all__ = [
    "BodySightedEvent",
    "BodyTrackedEvent",
    "CelestialEventBeganEvent",
    "ConstellationIdentifiedEvent",
    "SkyChangedEvent",
    "StargazedEvent",
    "WishMadeEvent",
]
