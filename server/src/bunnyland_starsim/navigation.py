"""Navigation by the stars.

When a character stands outdoors under a clear night sky, the circumpolar
:data:`~bunnyland_starsim.constellations.POLE_STAR` fixes due north. This prompt fragment
surfaces that cue, complementing a mapping/cartography pack: no compass required as long as
the stars are out.
"""

from __future__ import annotations

from relics import Entity, World

from .constellations import POLE_STAR
from .sky import derive_sky, stars_visible_from_room
from .spatial import room_of


def navigation_fragments(world: World, character: Entity) -> list[str]:
    """A cardinal-direction cue drawn from the pole star, when the stars are visible."""
    if character is None:
        return []
    sky = derive_sky(world)
    room = room_of(world, character.id)
    if not stars_visible_from_room(sky, room):
        return []
    return [f"{POLE_STAR} hangs fixed overhead, marking due north."]


__all__ = ["navigation_fragments"]
