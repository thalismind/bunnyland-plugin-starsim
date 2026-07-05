"""Telescope tiers: how faint a sky an optical aid can reach.

v1 modelled a telescope as a single ``power`` float that deepened a stargaze. v2 reads that
same ``power`` as a **tier**: a bigger aperture reaches a *fainter limiting magnitude*, so the
planets-and-comets tracking mechanic can gate a body behind the instrument needed to see it.

Magnitudes follow the astronomical convention — **smaller means brighter** — so a body is
within reach when its magnitude is *at most* the instrument's limiting magnitude. The naked
eye reaches :data:`NAKED_EYE_LIMIT`; each :class:`TelescopeTier` reaches deeper. Tier is a
pure function of ``power`` (a telescope carries no separate tier field), keeping ``power`` the
single source of truth and every v1 telescope untouched.
"""

from __future__ import annotations

from dataclasses import dataclass

from bunnyland.core import contents
from relics import Entity, World

from .components import TelescopeComponent

#: The faintest magnitude the unaided eye can pick out on a clear night.
NAKED_EYE_LIMIT = 4.0


@dataclass(frozen=True)
class TelescopeTier:
    """One instrument class: from ``min_power`` up, it reaches ``limiting_magnitude``."""

    name: str
    min_power: float
    limiting_magnitude: float


#: Instrument tiers in ascending aperture. A telescope's tier is the deepest one whose
#: ``min_power`` it meets; below the first tier it is no better than the naked eye.
TELESCOPE_TIERS: tuple[TelescopeTier, ...] = (
    TelescopeTier("spyglass", 1.0, 6.0),
    TelescopeTier("field telescope", 2.0, 9.0),
    TelescopeTier("great observatory", 3.0, 12.0),
)


def tier_for_power(power: float) -> TelescopeTier | None:
    """The deepest tier a telescope of ``power`` qualifies for, or ``None`` (naked-eye)."""
    best: TelescopeTier | None = None
    for tier in TELESCOPE_TIERS:
        if power >= tier.min_power and (best is None or tier.min_power > best.min_power):
            best = tier
    return best


def reach_magnitude(telescope: TelescopeComponent | None) -> float:
    """The faintest magnitude visible with ``telescope`` (or the naked eye when ``None``)."""
    if telescope is None:
        return NAKED_EYE_LIMIT
    tier = tier_for_power(telescope.power)
    return tier.limiting_magnitude if tier is not None else NAKED_EYE_LIMIT


def tier_name(telescope: TelescopeComponent | None) -> str:
    """A human label for the instrument in hand (``"naked eye"`` when there is none)."""
    if telescope is None:
        return "naked eye"
    tier = tier_for_power(telescope.power)
    return tier.name if tier is not None else "naked eye"


def held_telescope(world: World, character: Entity) -> TelescopeComponent | None:
    """Return the strongest telescope ``character`` is carrying, or ``None``."""
    best: TelescopeComponent | None = None
    for item_id in contents(character):
        if not world.has_entity(item_id):
            continue
        item = world.get_entity(item_id)
        if item.has_component(TelescopeComponent):
            telescope = item.get_component(TelescopeComponent)
            if best is None or telescope.power > best.power:
                best = telescope
    return best


__all__ = [
    "NAKED_EYE_LIMIT",
    "TELESCOPE_TIERS",
    "TelescopeTier",
    "held_telescope",
    "reach_magnitude",
    "tier_for_power",
    "tier_name",
]
