"""Spawn factories for starsim items.

The loader does not consume ``ContentContribution.prefabs``, so telescopes are created with
this ``spawn_entity`` helper (from tests, admin tooling, or a worldgen hook). A telescope is
a portable, holdable item carrying a :class:`TelescopeComponent`; pass ``room_id`` to drop it
into a room, or leave it out to spawn it uncontained (e.g. straight into an inventory).
"""

from __future__ import annotations

from bunnyland.core import (
    ContainmentMode,
    Contains,
    HoldableComponent,
    IdentityComponent,
    PortableComponent,
    spawn_entity,
)
from relics import Entity, World

from .components import TelescopeComponent
from .telescopes import TELESCOPE_TIERS


def _link_into_room(world: World, item: Entity, room_id) -> None:
    if room_id is None or not world.has_entity(room_id):
        return
    world.get_entity(room_id).add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), item.id)


def spawn_telescope(world: World, *, room_id=None, power: float = 1.0) -> Entity:
    """Spawn a holdable telescope item, optionally placed in ``room_id``."""
    item = spawn_entity(
        world,
        [
            IdentityComponent(name="telescope", kind="item", tags=("starsim",)),
            PortableComponent(),
            HoldableComponent(slot="hand"),
            TelescopeComponent(power=power),
        ],
    )
    _link_into_room(world, item, room_id)
    return item


def spawn_tiered_telescope(world: World, tier_name: str, *, room_id=None) -> Entity:
    """Spawn a telescope of a named tier (see :data:`TELESCOPE_TIERS`).

    Raises ``KeyError`` for an unknown tier name. The tier's ``min_power`` is used, so the
    spawned instrument reaches exactly that tier's limiting magnitude.
    """
    powers = {tier.name: tier.min_power for tier in TELESCOPE_TIERS}
    return spawn_telescope(world, room_id=room_id, power=powers[tier_name])


__all__ = ["spawn_telescope", "spawn_tiered_telescope"]
