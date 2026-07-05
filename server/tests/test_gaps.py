"""Coverage for the corners the v1 tests left open: no-clock rejections, dropped items,
non-first-person and empty prompt fragments, and the non-character mood guard."""

from __future__ import annotations

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    IdentityComponent,
    RoomComponent,
    WorldActor,
    WorldClockComponent,
    spawn_entity,
)
from bunnyland.core.commands import CommandCost, Lane, build_submitted_command
from bunnyland.core.components import AffectDelta
from bunnyland.core.handlers import HandlerContext
from bunnyland.prompts.context import ComponentPromptContext, PromptPerspective

from bunnyland_starsim import (
    ConstellationLogComponent,
    constellation_fragments,
    lift_mood,
    record_identified,
    spawn_telescope,
)
from bunnyland_starsim.celestial import MakeAWishHandler
from bunnyland_starsim.stargaze import StargazeHandler


def _clockless_world(command_type):
    """A room + character but no world clock, so the sky cannot be derived."""
    actor = WorldActor()
    for clock in list(actor.world.query().with_all([WorldClockComponent]).execute_entities()):
        actor.world.remove(clock.id)
    room = spawn_entity(actor.world, [RoomComponent(title="Field")])
    character = spawn_entity(
        actor.world, [IdentityComponent(name="Vin", kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    command = build_submitted_command(
        character_id=str(character.id),
        controller_id="ctrl",
        controller_generation=0,
        command_type=command_type,
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload={},
    )
    return actor, character, command


def test_stargaze_without_a_sky_is_rejected():
    actor, _character, command = _clockless_world("stargaze")
    result = StargazeHandler().execute(HandlerContext(world=actor.world, epoch=0), command)
    assert not result.ok
    assert result.reason == "there is no sky overhead"


def test_make_a_wish_without_a_sky_is_rejected():
    actor, _character, command = _clockless_world("make-a-wish")
    result = MakeAWishHandler().execute(HandlerContext(world=actor.world, epoch=0), command)
    assert not result.ok
    assert result.reason == "there is no sky overhead"


def test_stargaze_skips_a_dropped_telescope_item():
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Field")])
    character = spawn_entity(
        actor.world, [IdentityComponent(name="Vin", kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    ghost = spawn_telescope(actor.world, power=2.0)
    character.add_relationship(Contains(mode=ContainmentMode.INVENTORY), ghost.id)
    actor.world.remove(ghost.id)  # inventory link lingers past the entity

    command = build_submitted_command(
        character_id=str(character.id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="stargaze",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload={},
    )
    result = StargazeHandler().execute(HandlerContext(world=actor.world, epoch=0), command)
    assert result.ok  # the dead item is simply ignored


def test_stargaze_picks_the_strongest_of_mixed_inventory():
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Field")])
    character = spawn_entity(
        actor.world, [IdentityComponent(name="Vin", kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    # A non-telescope item (skipped), a strong scope, then a weaker one (does not displace).
    character.add_relationship(
        Contains(mode=ContainmentMode.INVENTORY),
        spawn_entity(actor.world, [IdentityComponent(name="rock", kind="item")]).id,
    )
    character.add_relationship(
        Contains(mode=ContainmentMode.INVENTORY), spawn_telescope(actor.world, power=3.0).id
    )
    character.add_relationship(
        Contains(mode=ContainmentMode.INVENTORY), spawn_telescope(actor.world, power=1.0).id
    )
    command = build_submitted_command(
        character_id=str(character.id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="stargaze",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload={},
    )
    result = StargazeHandler().execute(HandlerContext(world=actor.world, epoch=0), command)
    assert result.ok


def test_lift_mood_ignores_a_non_character():
    actor = WorldActor()
    rock = spawn_entity(actor.world, [IdentityComponent(name="rock", kind="item")])
    assert lift_mood(actor.world, rock, AffectDelta(valence=1.0), epoch=0) is None


def test_constellation_fragment_empty_when_nothing_charted():
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Field")])
    character = spawn_entity(
        actor.world, [IdentityComponent(name="Vin", kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    character.add_component(ConstellationLogComponent())  # present but empty
    assert constellation_fragments(actor.world, character) == []


def test_constellation_fragment_empty_in_third_person(monkeypatch):
    actor = WorldActor()
    room = spawn_entity(actor.world, [RoomComponent(title="Field")])
    character = spawn_entity(
        actor.world, [IdentityComponent(name="Vin", kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    record_identified(character, "the Pole Star")
    onlooker = spawn_entity(
        actor.world, [IdentityComponent(name="Onlooker", kind="character"), CharacterComponent()]
    )
    original = ComponentPromptContext.for_entity

    def as_onlooker(world, entity, **kwargs):
        return original(world, entity, perspective=PromptPerspective(viewer=onlooker))

    monkeypatch.setattr(ComponentPromptContext, "for_entity", staticmethod(as_onlooker))
    assert constellation_fragments(actor.world, character) == []
