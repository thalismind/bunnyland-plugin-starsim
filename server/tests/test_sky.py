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
from relics import World

from bunnyland_starsim import (
    NightSkyConsequence,
    SkyComponent,
    derive_sky,
    sky_fragments,
    stars_visible_from_room,
)
from bunnyland_starsim.events import SkyChangedEvent

SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR
NIGHT = 2 * SECONDS_PER_HOUR  # hour 2, day 1
DAY = 12 * SECONDS_PER_HOUR  # hour 12, day 1
METEOR_NIGHT = 13 * SECONDS_PER_DAY + NIGHT  # day 14, night
COMET_NIGHT = 41 * SECONDS_PER_DAY + NIGHT  # day 42, night


def _clock(actor):
    return list(actor.world.query().with_all([WorldClockComponent]).execute_entities())[0]


def _set_time(actor, seconds, *, condition=None):
    clock = _clock(actor)
    replace_component(clock, WorldClockComponent(game_time_seconds=seconds))
    if condition is not None:
        clock.add_component(WeatherComponent(condition=condition))
    return clock


def _room(actor, *, indoor=False):
    return spawn_entity(actor.world, [RoomComponent(title="Field", indoor=indoor)])


def _character(actor, room):
    character = spawn_entity(
        actor.world, [IdentityComponent(name="Vin", kind="character")]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return character


# -- derivation -------------------------------------------------------------------------


def test_default_clock_resolves_to_clear_night_with_stars():
    actor = WorldActor()  # bare clock at game_time_seconds=0 -> night
    sky = derive_sky(actor.world)
    assert sky.phase == "night"
    assert sky.condition == "clear"
    assert sky.stars_out is True


def test_daytime_has_no_stars():
    actor = WorldActor()
    _set_time(actor, DAY)
    sky = derive_sky(actor.world)
    assert sky.phase == "day"
    assert sky.stars_out is False


def test_clouds_hide_stars_at_night():
    actor = WorldActor()
    _set_time(actor, NIGHT, condition="cloudy")
    sky = derive_sky(actor.world)
    assert sky.phase == "night"
    assert sky.stars_out is False


def test_derive_sky_without_a_clock_is_none():
    assert derive_sky(World()) is None


def test_sky_is_deterministic():
    actor = WorldActor()
    _set_time(actor, METEOR_NIGHT)
    assert derive_sky(actor.world) == derive_sky(actor.world)


def test_meteor_shower_appears_on_its_day():
    actor = WorldActor()
    _set_time(actor, METEOR_NIGHT)
    assert derive_sky(actor.world).event == "meteor shower"


# -- room visibility --------------------------------------------------------------------


def test_stars_visible_from_outdoor_room_at_clear_night():
    actor = WorldActor()
    room = _room(actor, indoor=False)
    assert stars_visible_from_room(derive_sky(actor.world), room) is True


def test_stars_not_visible_indoors():
    actor = WorldActor()
    room = _room(actor, indoor=True)
    assert stars_visible_from_room(derive_sky(actor.world), room) is False


def test_stars_not_visible_in_daylight_outdoors():
    actor = WorldActor()
    _set_time(actor, DAY)
    room = _room(actor, indoor=False)
    assert stars_visible_from_room(derive_sky(actor.world), room) is False


def test_stars_not_visible_with_no_room():
    actor = WorldActor()
    assert stars_visible_from_room(derive_sky(actor.world), None) is False


def test_stars_not_visible_from_non_room_entity():
    actor = WorldActor()
    thing = spawn_entity(actor.world, [IdentityComponent(name="rock", kind="item")])
    assert stars_visible_from_room(derive_sky(actor.world), thing) is False


# -- consequence ------------------------------------------------------------------------


def test_consequence_stores_the_sky_singleton():
    actor = WorldActor()
    assert NightSkyConsequence().process(actor.world, 0) == []
    clock = _clock(actor)
    assert clock.has_component(SkyComponent)
    assert clock.get_component(SkyComponent).stars_out is True


def test_consequence_emits_event_when_a_shower_begins():
    actor = WorldActor()
    consequence = NightSkyConsequence()
    consequence.process(actor.world, 0)  # quiet night, stores sky
    _set_time(actor, METEOR_NIGHT)
    events = consequence.process(actor.world, 1)
    assert len(events) == 1
    assert isinstance(events[0], SkyChangedEvent)
    assert events[0].celestial_event == "meteor shower"


def test_consequence_emits_nothing_when_event_unchanged():
    actor = WorldActor()
    consequence = NightSkyConsequence()
    consequence.process(actor.world, 0)
    assert consequence.process(actor.world, 1) == []


def test_consequence_without_clock_is_empty():
    assert NightSkyConsequence().process(World(), 0) == []


# -- fragments --------------------------------------------------------------------------


def test_sky_fragments_describe_a_clear_night_outdoors():
    actor = WorldActor()
    room = _room(actor, indoor=False)
    character = _character(actor, room)
    lines = sky_fragments(actor.world, character)
    assert any("stars are out" in line for line in lines)
    assert any("the Pole Star" in line for line in lines)


def test_sky_fragments_mention_a_celestial_event():
    actor = WorldActor()
    _set_time(actor, COMET_NIGHT, condition="clear")  # pin clear weather over the comet
    room = _room(actor, indoor=False)
    character = _character(actor, room)
    lines = sky_fragments(actor.world, character)
    assert any("comet" in line for line in lines)


def test_sky_fragments_empty_indoors():
    actor = WorldActor()
    room = _room(actor, indoor=True)
    character = _character(actor, room)
    assert sky_fragments(actor.world, character) == []


def test_sky_fragments_empty_for_no_character():
    actor = WorldActor()
    assert sky_fragments(actor.world, None) == []
