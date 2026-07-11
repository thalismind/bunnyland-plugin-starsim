"""Planets and comets: a moving catalogue tracked across the nights.

Where :mod:`~bunnyland_starsim.constellations` are fixed figures, the **wanderers** move.
Each :class:`CelestialBody` — a planet or a comet — climbs above the horizon for a stretch of
its cycle and then sets again, all a pure function of the day number so the sky replays
identically. A body is *up* tonight when it is inside its visibility window; whether a given
gazer can actually resolve it additionally depends on its ``magnitude`` versus the reach of
the telescope in hand (see :mod:`~bunnyland_starsim.telescopes`).

Bodies are also **entities** in the world so a character can form a typed
:class:`~bunnyland_starsim.tracking.TracksBody` edge to one; :func:`ensure_bodies` spawns the
catalogue lazily and idempotently (only what is missing), keyed by name.
"""

from __future__ import annotations

from dataclasses import dataclass

from bunnyland.core import IdentityComponent, spawn_entity
from bunnyland.prompts.context import ComponentPromptContext
from pydantic.dataclasses import dataclass as pydantic_dataclass
from relics import Component, Entity, World

from .telescopes import NAKED_EYE_LIMIT

#: Body kinds.
PLANET = "planet"
COMET = "comet"


@dataclass(frozen=True)
class CelestialBody:
    """One wanderer. It is up when ``(day - 1 + offset) % period < window``.

    ``magnitude`` is astronomical (smaller is brighter); planets are bright and often up,
    comets faint and rarely so.
    """

    name: str
    kind: str
    magnitude: float
    period: int
    offset: int
    window: int
    lore: str


#: The full catalogue, four planets and two comets. Sorted by name for order-independence.
CATALOGUE: tuple[CelestialBody, ...] = (
    CelestialBody(
        "the Distant Wanderer",
        PLANET,
        magnitude=8.5,
        period=30,
        offset=0,
        window=15,
        lore="a dim blue-green speck creeping along the edge of sight",
    ),
    CelestialBody(
        "the Long-Tailed Visitor",
        COMET,
        magnitude=7.0,
        period=40,
        offset=0,
        window=3,
        lore="a smear of light dragging a ghostly tail",
    ),
    CelestialBody(
        "the Morning Lantern",
        PLANET,
        magnitude=-1.5,
        period=8,
        offset=0,
        window=5,
        lore="a brilliant point that leads the coming dawn",
    ),
    CelestialBody(
        "the Pale Wayfarer",
        COMET,
        magnitude=10.5,
        period=64,
        offset=0,
        window=2,
        lore="a barely-there haze that returns only on the long count",
    ),
    CelestialBody(
        "the Red Wanderer",
        PLANET,
        magnitude=1.0,
        period=12,
        offset=0,
        window=8,
        lore="a ruddy light that drifts slowly against the fixed stars",
    ),
    CelestialBody(
        "the Ringed Wanderer",
        PLANET,
        magnitude=5.5,
        period=20,
        offset=0,
        window=12,
        lore="a pale disc that hides faint rings from the naked eye",
    ),
)

#: Fast lookup by name.
_BY_NAME: dict[str, CelestialBody] = {b.name: b for b in CATALOGUE}


@pydantic_dataclass(frozen=True)
class CelestialBodyComponent(Component):
    """Marks an entity as a catalogued wanderer (a planet or comet)."""

    name: str = ""
    kind: str = PLANET
    magnitude: float = 0.0

    def prompt_fragments(self, ctx: ComponentPromptContext) -> tuple[str, ...]:
        return ()


def is_known_body(name: str) -> bool:
    """Whether ``name`` is a catalogued celestial body."""
    return name in _BY_NAME


def get_body(name: str) -> CelestialBody | None:
    """Return the catalogued body named ``name``, or ``None``."""
    return _BY_NAME.get(name)


def body_up(body: CelestialBody, day: int) -> bool:
    """Whether ``body`` is above the horizon on ``day`` (deterministic from the calendar)."""
    if day < 1:
        return False
    return (day - 1 + body.offset) % body.period < body.window


def bodies_up(day: int) -> tuple[CelestialBody, ...]:
    """All catalogued bodies above the horizon on ``day``, sorted by name."""
    return tuple(sorted((b for b in CATALOGUE if body_up(b, day)), key=lambda b: b.name))


def observable_bodies(day: int, reach: float) -> tuple[CelestialBody, ...]:
    """Bodies up on ``day`` and bright enough for an instrument reaching ``reach`` magnitude."""
    return tuple(b for b in bodies_up(day) if b.magnitude <= reach)


def naked_eye_bodies(day: int) -> tuple[CelestialBody, ...]:
    """Bodies up on ``day`` that need no telescope at all."""
    return observable_bodies(day, NAKED_EYE_LIMIT)


def sky_bodies_fragments(world: World, character: Entity) -> list[str]:
    """Name the naked-eye wanderers up tonight, when the stars are visible to ``character``."""
    if character is None:
        return []
    # Imported here to avoid a load-time cycle: sky/spatial depend on this pack's siblings.
    from .sky import derive_sky, stars_visible_from_room
    from .spatial import room_of

    sky = derive_sky(world)
    room = room_of(world, character.id)
    if not stars_visible_from_room(sky, room):
        return []
    up = naked_eye_bodies(sky.day)
    if not up:
        return []
    names = ", ".join(b.name for b in up)
    return [f"Among the fixed stars, {names} wander overhead."]


def ensure_bodies(world: World) -> dict[str, Entity]:
    """Spawn any missing catalogue bodies as entities; return the name -> entity map.

    Idempotent: an existing body entity (matched by name) is reused, never duplicated.
    """
    existing: dict[str, Entity] = {}
    for entity in world.query().with_all([CelestialBodyComponent]).execute_entities():
        existing[entity.get_component(CelestialBodyComponent).name] = entity
    for body in CATALOGUE:
        if body.name in existing:
            continue
        entity = spawn_entity(
            world,
            [
                IdentityComponent(name=body.name, kind="celestial-body", tags=("starsim",)),
                CelestialBodyComponent(name=body.name, kind=body.kind, magnitude=body.magnitude),
            ],
        )
        existing[body.name] = entity
    return existing


__all__ = [
    "CATALOGUE",
    "COMET",
    "PLANET",
    "CelestialBody",
    "CelestialBodyComponent",
    "bodies_up",
    "body_up",
    "ensure_bodies",
    "get_body",
    "is_known_body",
    "naked_eye_bodies",
    "observable_bodies",
    "sky_bodies_fragments",
]
