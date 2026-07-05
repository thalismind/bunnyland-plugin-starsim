from __future__ import annotations

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    IdentityComponent,
    RoomComponent,
    WorldActor,
    spawn_entity,
)

from bunnyland_starsim import holder_of, room_of


def _room(world):
    return spawn_entity(world, [RoomComponent(title="Field")])


def _character(world):
    return spawn_entity(
        world, [IdentityComponent(name="Vin", kind="character"), CharacterComponent()]
    )


def _item(world, name="thing"):
    return spawn_entity(world, [IdentityComponent(name=name, kind="item")])


# -- holder_of --------------------------------------------------------------------------


def test_holder_of_missing_item_is_none():
    actor = WorldActor()
    assert holder_of(actor.world, "entity_9999") is None


def test_holder_of_loose_item_in_a_room_is_none():
    actor = WorldActor()
    room = _room(actor.world)
    item = _item(actor.world)
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), item.id)
    assert holder_of(actor.world, item.id) is None


def test_holder_of_uncontained_item_is_none():
    actor = WorldActor()
    item = _item(actor.world)
    assert holder_of(actor.world, item.id) is None


def test_holder_of_carried_item_returns_the_carrier():
    actor = WorldActor()
    character = _character(actor.world)
    item = _item(actor.world)
    character.add_relationship(Contains(mode=ContainmentMode.INVENTORY), item.id)
    holder = holder_of(actor.world, item.id)
    assert holder is not None and holder.id == character.id


# -- room_of ----------------------------------------------------------------------------


def test_room_of_missing_entity_is_none():
    actor = WorldActor()
    assert room_of(actor.world, "entity_9999") is None


def test_room_of_uncontained_entity_is_none():
    actor = WorldActor()
    assert room_of(actor.world, _item(actor.world).id) is None


def test_room_of_direct_occupant():
    actor = WorldActor()
    room = _room(actor.world)
    character = _character(actor.world)
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    found = room_of(actor.world, character.id)
    assert found is not None and found.id == room.id


def test_room_of_resolves_through_a_carrier():
    actor = WorldActor()
    room = _room(actor.world)
    character = _character(actor.world)
    item = _item(actor.world)
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    character.add_relationship(Contains(mode=ContainmentMode.INVENTORY), item.id)
    found = room_of(actor.world, item.id)  # walks item -> carrier -> room
    assert found is not None and found.id == room.id


def test_room_of_guards_against_a_containment_cycle():
    actor = WorldActor()
    a = _item(actor.world, "a")
    b = _item(actor.world, "b")
    a.add_relationship(Contains(mode=ContainmentMode.INVENTORY), b.id)
    b.add_relationship(Contains(mode=ContainmentMode.INVENTORY), a.id)
    # No room anywhere on the loop: the depth guard returns None rather than spinning.
    assert room_of(actor.world, a.id) is None
