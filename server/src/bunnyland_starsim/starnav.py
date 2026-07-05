"""Navigate by the stars — a safe, optional tie-in with a cartography pack.

Star navigation already stands alone (see :mod:`~bunnyland_starsim.navigation`): the pole star
fixes due north whenever the stars are out. This module adds an *optional* enhancement — when a
cartography pack is loaded and the gazer is holding its compass, the pole star **corroborates**
the compass bearing. It is wired through a **safe conditional import**: if
``bunnyland_cartographysim`` is not installed the symbol is simply ``None`` and the enhancement
stays dormant, so starsim runs fully standalone. Nothing here reaches into another pack's state
beyond checking for its public component on a held item.
"""

from __future__ import annotations

import logging

from bunnyland.core import contents
from relics import Entity, World

from .constellations import POLE_STAR
from .sky import derive_sky, stars_visible_from_room
from .spatial import room_of

LOG = logging.getLogger(__name__)

try:  # optional synergy: only active when the cartography pack is installed
    from bunnyland_cartographysim import CompassComponent
except ImportError:  # pragma: no cover - exercised via a monkeypatched symbol in tests
    CompassComponent = None
    LOG.warning(
        "bunnyland_cartographysim not installed; star/compass corroboration disabled "
        "(starsim runs standalone)"
    )


def _holds_compass(world: World, character: Entity) -> bool:
    if CompassComponent is None:
        return False
    for item_id in contents(character):
        if world.has_entity(item_id) and world.get_entity(item_id).has_component(CompassComponent):
            return True
    return False


def star_compass_fragments(world: World, character: Entity) -> list[str]:
    """When a compass is in hand under a clear night sky, note the pole star confirms it.

    Dormant (returns ``[]``) whenever the cartography pack is absent, so the pack is safe to
    load on its own.
    """
    if character is None:
        return []
    sky = derive_sky(world)
    room = room_of(world, character.id)
    if not stars_visible_from_room(sky, room):
        return []
    if not _holds_compass(world, character):
        return []
    return [f"{POLE_STAR} confirms the bearing your compass shows."]


__all__ = ["star_compass_fragments"]
