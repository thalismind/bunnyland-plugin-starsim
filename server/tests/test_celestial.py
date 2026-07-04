from __future__ import annotations

from bunnyland.core import (
    CharacterComponent,
    ContainmentMode,
    Contains,
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
from bunnyland.mechanics.environment import WeatherComponent

from bunnyland_starsim import WishLogComponent, celestial_event_for
from bunnyland_starsim.celestial import (
    COMET,
    COMET_DAY_OF_YEAR,
    DAYS_PER_YEAR,
    METEOR_SHOWER,
    METEOR_SHOWER_PERIOD,
    MakeAWishHandler,
)
from bunnyland_starsim.events import WishMadeEvent

SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR
NIGHT = 2 * SECONDS_PER_HOUR
DAY = 12 * SECONDS_PER_HOUR


def _night_of(day, hour_seconds=NIGHT):
    return (day - 1) * SECONDS_PER_DAY + hour_seconds


def _world(*, day=14, indoor=False, seconds=None, condition="clear"):
    # The calendar-driven weather cycle makes some event days cloudy on their own; scenario
    # tests pin the weather explicitly so the sky's day/night/event axis is isolated.
    actor = WorldActor()
    clock = list(actor.world.query().with_all([WorldClockComponent]).execute_entities())[0]
    replace_component(
        clock,
        WorldClockComponent(
            game_time_seconds=seconds if seconds is not None else _night_of(day)
        ),
    )
    clock.add_component(WeatherComponent(condition=condition))
    room = spawn_entity(actor.world, [RoomComponent(title="Field", indoor=indoor)])
    character = spawn_entity(
        actor.world, [IdentityComponent(name="Vin", kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return actor, room, character


def _cmd(character_id):
    return build_submitted_command(
        character_id=str(character_id),
        controller_id="ctrl",
        controller_generation=0,
        command_type="make-a-wish",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload={},
    )


def _ctx(actor):
    return HandlerContext(world=actor.world, epoch=0)


# -- deterministic calendar -------------------------------------------------------------


def test_meteor_shower_on_period_days():
    assert celestial_event_for(METEOR_SHOWER_PERIOD) == METEOR_SHOWER
    assert celestial_event_for(2 * METEOR_SHOWER_PERIOD) == METEOR_SHOWER


def test_comet_takes_precedence_on_its_day():
    assert celestial_event_for(COMET_DAY_OF_YEAR) == COMET


def test_quiet_days_have_no_event():
    assert celestial_event_for(1) == ""
    assert celestial_event_for(3) == ""


def test_events_recur_every_year():
    assert celestial_event_for(COMET_DAY_OF_YEAR + DAYS_PER_YEAR) == COMET


def test_non_positive_day_is_quiet():
    assert celestial_event_for(0) == ""


def test_event_lookup_is_deterministic():
    assert celestial_event_for(14) == celestial_event_for(14)


# -- make-a-wish happy path -------------------------------------------------------------


def test_wish_during_a_meteor_shower_succeeds():
    actor, _room, character = _world(day=14)
    result = MakeAWishHandler().execute(_ctx(actor), _cmd(character.id))
    assert result.ok
    assert isinstance(result.events[0], WishMadeEvent)
    assert result.events[0].celestial_event == METEOR_SHOWER


def test_wish_records_the_wish_and_lifts_mood():
    actor, _room, character = _world(day=14)
    MakeAWishHandler().execute(_ctx(actor), _cmd(character.id))
    assert character.get_component(WishLogComponent).wishes == 1
    thoughts = list(actor.world.query().with_all([ThoughtComponent]).execute_entities())
    assert len(thoughts) == 1
    assert thoughts[0].get_component(ThoughtComponent).affect_delta.confidence > 0


def test_repeated_wishes_accumulate():
    actor, _room, character = _world(day=14)
    handler = MakeAWishHandler()
    handler.execute(_ctx(actor), _cmd(character.id))
    handler.execute(_ctx(actor), _cmd(character.id))
    assert character.get_component(WishLogComponent).wishes == 2


def test_wish_during_a_comet_succeeds():
    actor, _room, character = _world(day=COMET_DAY_OF_YEAR)
    result = MakeAWishHandler().execute(_ctx(actor), _cmd(character.id))
    assert result.ok
    assert result.events[0].celestial_event == COMET


# -- make-a-wish rejections -------------------------------------------------------------


def test_rejects_invalid_character_id():
    actor, _room, _character = _world(day=14)
    result = MakeAWishHandler().execute(_ctx(actor), _cmd("???"))
    assert not result.ok
    assert result.reason == "invalid character id"


def test_rejects_character_with_no_room():
    actor = WorldActor()
    clock = list(actor.world.query().with_all([WorldClockComponent]).execute_entities())[0]
    replace_component(clock, WorldClockComponent(game_time_seconds=_night_of(14)))
    character = spawn_entity(
        actor.world, [IdentityComponent(name="drifter", kind="character"), CharacterComponent()]
    )
    result = MakeAWishHandler().execute(_ctx(actor), _cmd(character.id))
    assert not result.ok
    assert result.reason == "you are not in a room"


def test_rejects_when_no_event_overhead():
    actor, _room, character = _world(day=1)  # quiet night
    result = MakeAWishHandler().execute(_ctx(actor), _cmd(character.id))
    assert not result.ok
    assert result.reason == "there is nothing to wish upon right now"


def test_rejects_indoors_even_during_a_shower():
    actor, _room, character = _world(day=14, indoor=True)
    result = MakeAWishHandler().execute(_ctx(actor), _cmd(character.id))
    assert not result.ok
    assert result.reason == "you are indoors; you cannot see the sky"


def test_rejects_in_daylight():
    actor, _room, character = _world(seconds=13 * SECONDS_PER_DAY + DAY)  # day 14, noon
    result = MakeAWishHandler().execute(_ctx(actor), _cmd(character.id))
    assert not result.ok
    assert result.reason == "the stars are not out"


def test_rejects_under_clouds():
    actor, _room, character = _world(day=14, condition="overcast")
    result = MakeAWishHandler().execute(_ctx(actor), _cmd(character.id))
    assert not result.ok
    assert result.reason == "clouds hide the stars"
