from __future__ import annotations

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    IdentityComponent,
    WorldActor,
    spawn_entity,
)

from bunnyland_starsim import spawn_telescope, spawn_tiered_telescope
from bunnyland_starsim.components import TelescopeComponent
from bunnyland_starsim.telescopes import (
    NAKED_EYE_LIMIT,
    TELESCOPE_TIERS,
    held_telescope,
    reach_magnitude,
    tier_for_power,
    tier_name,
)


def _character(world):
    return spawn_entity(
        world, [IdentityComponent(name="Vin", kind="character"), CharacterComponent()]
    )


def _hold(holder, item):
    holder.add_relationship(Contains(mode=ContainmentMode.INVENTORY), item.id)


# -- tier resolution --------------------------------------------------------------------


def test_below_first_tier_is_naked_eye():
    assert tier_for_power(0.5) is None
    assert reach_magnitude(TelescopeComponent(power=0.5)) == NAKED_EYE_LIMIT
    assert tier_name(TelescopeComponent(power=0.5)) == "naked eye"


def test_each_tier_reaches_its_limiting_magnitude():
    assert tier_for_power(1.0).name == "spyglass"
    assert tier_for_power(2.0).name == "field telescope"
    assert tier_for_power(3.0).name == "great observatory"
    # A power between tiers falls back to the deepest one it clears.
    assert tier_for_power(2.5).name == "field telescope"
    assert tier_for_power(99.0).name == "great observatory"


def test_reach_magnitude_deepens_with_the_tier():
    reaches = [reach_magnitude(TelescopeComponent(power=t.min_power)) for t in TELESCOPE_TIERS]
    assert reaches == sorted(reaches)
    assert reaches[-1] > reaches[0] > NAKED_EYE_LIMIT


def test_naked_eye_when_no_instrument():
    assert reach_magnitude(None) == NAKED_EYE_LIMIT
    assert tier_name(None) == "naked eye"


# -- held_telescope ---------------------------------------------------------------------


def test_no_telescope_in_hand_is_none():
    actor = WorldActor()
    character = _character(actor.world)
    assert held_telescope(actor.world, character) is None


def test_non_telescope_items_are_ignored():
    actor = WorldActor()
    character = _character(actor.world)
    _hold(character, spawn_entity(actor.world, [IdentityComponent(name="rock", kind="item")]))
    assert held_telescope(actor.world, character) is None


def test_strongest_telescope_wins():
    actor = WorldActor()
    character = _character(actor.world)
    _hold(character, spawn_telescope(actor.world, power=1.0))
    _hold(character, spawn_telescope(actor.world, power=3.0))
    _hold(character, spawn_telescope(actor.world, power=0.5))  # a weaker one does not displace it
    best = held_telescope(actor.world, character)
    assert best is not None and best.power == 3.0


def test_a_dropped_item_id_is_skipped():
    actor = WorldActor()
    character = _character(actor.world)
    scope = spawn_telescope(actor.world, power=2.0)
    _hold(character, scope)
    actor.world.remove(scope.id)  # inventory link lingers but the entity is gone
    assert held_telescope(actor.world, character) is None


# -- prefabs ----------------------------------------------------------------------------


def test_spawn_tiered_telescope_uses_the_tier_min_power():
    actor = WorldActor()
    scope = spawn_tiered_telescope(actor.world, "field telescope")
    assert scope.get_component(TelescopeComponent).power == 2.0


def test_spawn_tiered_telescope_unknown_tier_raises():
    actor = WorldActor()
    try:
        spawn_tiered_telescope(actor.world, "hubble")
    except KeyError:
        return
    raise AssertionError("expected KeyError for an unknown tier")
