import asyncio

from bunnyland.core import Contains, WorldActor
from bunnyland.plugins import apply_plugins
from bunnyland.worldgen import RoomSpec, WorldProposal, instantiate

from bunnyland_starsim import TelescopeComponent
from bunnyland_starsim.plugin import bunnyland_plugins as _plugins


def _room(spec):
    actor = WorldActor()
    apply_plugins(_plugins(), actor)
    result = asyncio.run(instantiate(actor, WorldProposal(seed="seed", rooms=[spec])))
    room = actor.world.get_entity(result.rooms[spec.key])
    scopes = [
        actor.world.get_entity(target)
        for _edge, target in room.get_relationships(Contains)
        if actor.world.get_entity(target).has_component(TelescopeComponent)
    ]
    return scopes


def test_observatory_room_gets_one_telescope():
    scopes = _room(RoomSpec(key="observatory", title="Old Observatory"))
    assert len(scopes) == 1
    assert scopes[0].get_component(TelescopeComponent).power > 0


def test_vantage_detected_from_biome_description_or_tags():
    assert _room(RoomSpec(key="peak", title="Peak", biome="hilltop"))
    assert _room(RoomSpec(key="perch", title="Perch", description="a watchtower"))
    assert _room(RoomSpec(key="deck", title="Deck", tags=("rooftop",)))


def test_plain_room_gets_no_telescope():
    assert _room(RoomSpec(key="cellar", title="Cellar")) == []
