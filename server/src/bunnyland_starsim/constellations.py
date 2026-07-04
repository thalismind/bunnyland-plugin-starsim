"""Constellations: a fixed catalogue, some circumpolar and some seasonal.

Every constellation is either **circumpolar** (``season is None`` — up every clear night) or
**seasonal** (visible only during its season), so the sky rewards returning across the year.
The whole catalogue is static data, which keeps the visible sky deterministic: given a
season, exactly one sorted set of constellations is up.

:class:`~bunnyland_starsim.components.ConstellationLogComponent` records which of them a
character has charted; the ``stargaze`` verb adds to it.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from bunnyland.core.ecs import replace_component
from bunnyland.prompts.context import ComponentPromptContext
from relics import Entity, World

from .components import ConstellationLogComponent

#: The circumpolar star that never sets — the anchor for navigation by the sky.
POLE_STAR = "the Pole Star"


@dataclass(frozen=True)
class Constellation:
    """One constellation. ``season`` is ``None`` for a circumpolar (always-up) figure."""

    name: str
    season: str | None
    lore: str


#: The full catalogue. Circumpolar figures first, then two per season.
CATALOGUE: tuple[Constellation, ...] = (
    Constellation(POLE_STAR, None, "a fixed point marking due north"),
    Constellation("the Lantern", None, "a steady lamp that circles the pole"),
    Constellation("the Hare", "spring", "a leaping form that heralds the thaw"),
    Constellation("the Bramble", "spring", "a tangle of faint stars low in the east"),
    Constellation("the Kiln", "summer", "a red-tinged cluster that burns at midnight"),
    Constellation("the River", "summer", "a long stream of stars spilling to the horizon"),
    Constellation("the Sickle", "autumn", "a curved blade rising over the harvest"),
    Constellation("the Hound", "autumn", "a loyal shape that trails the Sickle"),
    Constellation("the Warren", "winter", "a huddle of dim stars against the cold"),
    Constellation("the Crown", "winter", "a ring of bright points high overhead"),
)

#: Fast lookup by name.
_BY_NAME: dict[str, Constellation] = {c.name: c for c in CATALOGUE}


def constellations_up(season: str) -> tuple[str, ...]:
    """Sorted names of the constellations visible on a clear night in ``season``."""
    names = [c.name for c in CATALOGUE if c.season is None or c.season == season]
    return tuple(sorted(names))


def is_known_constellation(name: str) -> bool:
    """Whether ``name`` is a catalogued constellation."""
    return name in _BY_NAME


def record_identified(character: Entity, name: str) -> bool:
    """Add ``name`` to a character's log, creating the component if needed.

    Returns ``True`` if this was a *new* identification, ``False`` if already charted.
    """
    log = (
        character.get_component(ConstellationLogComponent)
        if character.has_component(ConstellationLogComponent)
        else ConstellationLogComponent()
    )
    if name in log.identified:
        return False
    identified = tuple(sorted({*log.identified, name}))
    if character.has_component(ConstellationLogComponent):
        replace_component(character, replace(log, identified=identified))
    else:
        character.add_component(ConstellationLogComponent(identified=identified))
    return True


def constellation_fragments(world: World, character: Entity) -> list[str]:
    """First-person line listing the constellations the character has charted."""
    if character is None or not character.has_component(ConstellationLogComponent):
        return []
    ctx = ComponentPromptContext.for_entity(world, character)
    if not ctx.is_first_person:
        return []
    identified = character.get_component(ConstellationLogComponent).identified
    if not identified:
        return []
    return [f"You have charted {len(identified)} constellations: {', '.join(identified)}."]


__all__ = [
    "CATALOGUE",
    "POLE_STAR",
    "Constellation",
    "constellation_fragments",
    "constellations_up",
    "is_known_constellation",
    "record_identified",
]
