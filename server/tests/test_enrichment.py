from __future__ import annotations

import asyncio

from bunnyland.core import (
    ContainmentMode,
    Contains,
    IdentityComponent,
    RoomComponent,
    WorldActor,
    contents,
    spawn_entity,
)
from bunnyland.core.components import GenerationIntentComponent
from bunnyland.core.events import RoomGeneratedEvent, event_base
from bunnyland.plugins import apply_plugins, load_modules

from bunnyland_starsim.components import TelescopeComponent


def _actor():
    actor = WorldActor()
    apply_plugins(load_modules(["bunnyland_starsim"]), actor)
    return actor


def _publish(actor, event):
    asyncio.run(actor.bus.publish(event))


def _room(actor, *, room_key="chamber", biome="plains", description="", tags=(), entity_id=None):
    entity = spawn_entity(actor.world, [RoomComponent(title=room_key, biome=biome)])
    _publish(
        actor,
        RoomGeneratedEvent(
            **event_base(0),
            seed="seed",
            entity_id=entity_id if entity_id is not None else str(entity.id),
            entity_key=room_key,
            entity_kind="room",
            generation=GenerationIntentComponent(description=description, tags=tuple(tags)),
            room_key=room_key,
            biome=biome,
            indoor=False,
        ),
    )
    return entity


def _telescopes_in(world, room):
    return [
        world.get_entity(i)
        for i in contents(room)
        if world.has_entity(i) and world.get_entity(i).has_component(TelescopeComponent)
    ]


def test_observatory_room_gets_a_telescope():
    actor = _actor()
    room = _room(actor, room_key="the old observatory")
    scopes = _telescopes_in(actor.world, room)
    assert len(scopes) == 1
    assert scopes[0].get_component(TelescopeComponent).power == 2.0  # a field telescope


def test_vantage_detected_from_biome_or_description_or_tags():
    actor = _actor()
    by_biome = _room(actor, room_key="peak", biome="windswept hilltop")
    by_desc = _room(actor, room_key="perch", description="a lonely watchtower over the valley")
    by_tags = _room(actor, room_key="deck", tags=("rooftop", "quiet"))
    assert _telescopes_in(actor.world, by_biome)
    assert _telescopes_in(actor.world, by_desc)
    assert _telescopes_in(actor.world, by_tags)


def test_vantage_with_other_contents_still_gets_exactly_one_telescope():
    actor = _actor()
    entity = spawn_entity(actor.world, [RoomComponent(title="observatory", biome="stone")])
    # A pre-existing non-telescope item must be skipped, not mistaken for a scope.
    entity.add_relationship(
        Contains(mode=ContainmentMode.ROOM_CONTENT),
        spawn_entity(actor.world, [IdentityComponent(name="dusty ledger", kind="item")]).id,
    )
    _publish(
        actor,
        RoomGeneratedEvent(
            **event_base(0),
            seed="seed",
            entity_id=str(entity.id),
            entity_key="observatory",
            entity_kind="room",
            generation=GenerationIntentComponent(),
            room_key="observatory",
            biome="stone",
            indoor=False,
        ),
    )
    assert len(_telescopes_in(actor.world, entity)) == 1


def test_ordinary_room_gets_no_telescope():
    actor = _actor()
    room = _room(actor, room_key="mud kitchen", biome="swamp")
    assert _telescopes_in(actor.world, room) == []


def test_seeding_is_idempotent():
    actor = _actor()
    entity = spawn_entity(actor.world, [RoomComponent(title="tower", biome="stone")])
    event = RoomGeneratedEvent(
        **event_base(0),
        seed="seed",
        entity_id=str(entity.id),
        entity_key="tower",
        entity_kind="room",
        generation=GenerationIntentComponent(),
        room_key="tower",
        biome="stone",
        indoor=False,
    )
    _publish(actor, event)
    _publish(actor, event)  # a second generation of the same room must not double up
    assert len(_telescopes_in(actor.world, entity)) == 1


def test_unknown_entity_id_is_ignored():
    actor = _actor()
    # A vantage room_key but a dangling entity id: the hook bails before touching the world.
    _publish(
        actor,
        RoomGeneratedEvent(
            **event_base(0),
            seed="seed",
            entity_id="entity_999999",
            entity_key="observatory",
            entity_kind="room",
            generation=GenerationIntentComponent(),
            room_key="observatory",
            biome="stone",
            indoor=False,
        ),
    )
    telescopes = list(actor.world.query().with_all([TelescopeComponent]).execute_entities())
    assert telescopes == []
