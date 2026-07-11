from __future__ import annotations

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
    HasThought,
    IdentityComponent,
    RoomComponent,
    ThoughtComponent,
    WorldActor,
    WorldClockComponent,
    replace_component,
    spawn_entity,
)
from bunnyland.core.commands import CommandCost, Lane, build_submitted_command
from bunnyland.core.handlers import HandlerContext
from bunnyland.foundation.environment.mechanics import WeatherComponent

from bunnyland_starsim import ConstellationLogComponent, spawn_telescope
from bunnyland_starsim.events import ConstellationIdentifiedEvent, StargazedEvent
from bunnyland_starsim.stargaze import StargazeHandler

DAY = 12 * 3600


def _world(*, indoor=False, seconds=None, condition=None):
    actor = WorldActor()
    if seconds is not None or condition is not None:
        clock = list(actor.world.query().with_all([WorldClockComponent]).execute_entities())[0]
        if seconds is not None:
            replace_component(clock, WorldClockComponent(game_time_seconds=seconds))
        if condition is not None:
            clock.add_component(WeatherComponent(condition=condition))
    room = spawn_entity(actor.world, [RoomComponent(title="Field", indoor=indoor)])
    character = spawn_entity(
        actor.world, [IdentityComponent(name="Vin", kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return actor, room, character


def _hold(holder, item):
    holder.add_relationship(Contains(mode=ContainmentMode.INVENTORY), item.id)


def _cmd(character_id, payload=None):
    return build_submitted_command(
        character_id=str(character_id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="stargaze",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload=payload or {},
    )


def _ctx(actor):
    return HandlerContext(world=actor.world, epoch=0)


def _thoughts(actor):
    return list(actor.world.query().with_all([ThoughtComponent]).execute_entities())


# -- happy paths ------------------------------------------------------------------------


def test_stargaze_outdoors_at_night_succeeds():
    actor, _room, character = _world()
    result = StargazeHandler().execute(_ctx(actor), _cmd(character.id))
    assert result.ok
    assert isinstance(result.events[0], StargazedEvent)


def test_stargaze_lifts_mood():
    actor, _room, character = _world()
    StargazeHandler().execute(_ctx(actor), _cmd(character.id))
    thoughts = _thoughts(actor)
    assert len(thoughts) == 1
    assert thoughts[0].get_component(ThoughtComponent).affect_delta.valence > 0
    assert list(character.get_relationships(HasThought))


def test_charting_a_visible_constellation_logs_it():
    actor, _room, character = _world()
    result = StargazeHandler().execute(
        _ctx(actor), _cmd(character.id, {"constellation": "the Hare"})
    )
    assert result.ok
    assert any(isinstance(e, ConstellationIdentifiedEvent) for e in result.events)
    assert character.get_component(ConstellationLogComponent).identified == ("the Hare",)


def test_recharting_a_known_constellation_emits_no_identify_event():
    actor, _room, character = _world()
    handler = StargazeHandler()
    handler.execute(_ctx(actor), _cmd(character.id, {"constellation": "the Hare"}))
    result = handler.execute(_ctx(actor), _cmd(character.id, {"constellation": "the Hare"}))
    assert result.ok
    assert not any(isinstance(e, ConstellationIdentifiedEvent) for e in result.events)


def test_telescope_deepens_the_mood_lift():
    plain_actor, _r1, plain = _world()
    scope_actor, _r2, gazer = _world()
    _hold(gazer, spawn_telescope(scope_actor.world))

    StargazeHandler().execute(_ctx(plain_actor), _cmd(plain.id))
    StargazeHandler().execute(_ctx(scope_actor), _cmd(gazer.id))

    plain_valence = _thoughts(plain_actor)[0].get_component(ThoughtComponent).affect_delta.valence
    scope_valence = _thoughts(scope_actor)[0].get_component(ThoughtComponent).affect_delta.valence
    assert scope_valence > plain_valence


# -- rejections -------------------------------------------------------------------------


def test_rejects_invalid_character_id():
    actor, _room, _character = _world()
    result = StargazeHandler().execute(_ctx(actor), _cmd("???"))
    assert not result.ok
    assert result.reason == "invalid character id"


def test_rejects_missing_character():
    actor, _room, _character = _world()
    result = StargazeHandler().execute(_ctx(actor), _cmd("entity_9999"))
    assert not result.ok
    assert result.reason == "character does not exist"


def test_rejects_character_with_no_room():
    actor = WorldActor()
    character = spawn_entity(
        actor.world, [IdentityComponent(name="drifter", kind="character"), CharacterComponent()]
    )
    result = StargazeHandler().execute(_ctx(actor), _cmd(character.id))
    assert not result.ok
    assert result.reason == "you are not in a room"


def test_rejects_indoors():
    actor, _room, character = _world(indoor=True)
    result = StargazeHandler().execute(_ctx(actor), _cmd(character.id))
    assert not result.ok
    assert result.reason == "you are indoors; you cannot see the sky"


def test_rejects_in_daylight():
    actor, _room, character = _world(seconds=DAY)
    result = StargazeHandler().execute(_ctx(actor), _cmd(character.id))
    assert not result.ok
    assert result.reason == "the stars are not out"


def test_rejects_under_clouds():
    actor, _room, character = _world(condition="cloudy")
    result = StargazeHandler().execute(_ctx(actor), _cmd(character.id))
    assert not result.ok
    assert result.reason == "clouds hide the stars"


def test_rejects_unknown_constellation():
    actor, _room, character = _world()
    result = StargazeHandler().execute(
        _ctx(actor), _cmd(character.id, {"constellation": "the Toaster"})
    )
    assert not result.ok
    assert result.reason == "that is not a constellation you know of"


def test_rejects_out_of_season_constellation():
    actor, _room, character = _world()  # spring night
    result = StargazeHandler().execute(
        _ctx(actor),
        _cmd(character.id, {"constellation": "the Kiln"}),  # summer figure
    )
    assert not result.ok
    assert result.reason == "that constellation is not visible tonight"
