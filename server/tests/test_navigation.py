from __future__ import annotations

from bunnyland.core import (
    ContainmentMode,
    Contains,
    IdentityComponent,
    RoomComponent,
    WorldActor,
    WorldClockComponent,
    replace_component,
    spawn_entity,
)
from bunnyland.mechanics.environment import WeatherComponent

from bunnyland_starsim import POLE_STAR, navigation_fragments

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
    character = spawn_entity(actor.world, [IdentityComponent(name="Vin", kind="character")])
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return actor, character


def test_pole_star_marks_north_outdoors_at_night():
    actor, character = _world()
    lines = navigation_fragments(actor.world, character)
    assert len(lines) == 1
    assert POLE_STAR in lines[0]
    assert "north" in lines[0]


def test_no_cue_indoors():
    actor, character = _world(indoor=True)
    assert navigation_fragments(actor.world, character) == []


def test_no_cue_in_daylight():
    actor, character = _world(seconds=DAY)
    assert navigation_fragments(actor.world, character) == []


def test_no_cue_under_clouds():
    actor, character = _world(condition="cloudy")
    assert navigation_fragments(actor.world, character) == []


def test_no_cue_for_missing_character():
    actor, _character = _world()
    assert navigation_fragments(actor.world, None) == []
