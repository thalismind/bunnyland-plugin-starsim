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

from bunnyland_starsim.bodies import (
    CATALOGUE,
    CelestialBodyComponent,
    bodies_up,
    body_up,
    ensure_bodies,
    get_body,
    is_known_body,
    naked_eye_bodies,
    observable_bodies,
    sky_bodies_fragments,
)
from bunnyland_starsim.telescopes import NAKED_EYE_LIMIT

SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR
NIGHT = 2 * SECONDS_PER_HOUR


def _night(day):
    return (day - 1) * SECONDS_PER_DAY + NIGHT


def _outdoor_world(*, day=1, condition="clear", indoor=False):
    actor = WorldActor()
    clock = list(actor.world.query().with_all([WorldClockComponent]).execute_entities())[0]
    replace_component(clock, WorldClockComponent(game_time_seconds=_night(day)))
    clock.add_component(WeatherComponent(condition=condition))
    room = spawn_entity(actor.world, [RoomComponent(title="Hill", indoor=indoor)])
    character = spawn_entity(actor.world, [IdentityComponent(name="Vin", kind="character")])
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return actor, character


# -- catalogue lookups ------------------------------------------------------------------


def test_known_and_unknown_bodies():
    assert is_known_body("the Red Wanderer")
    assert not is_known_body("the Death Star")
    assert get_body("the Red Wanderer").kind == "planet"
    assert get_body("the Death Star") is None


def test_body_up_is_calendar_driven():
    morning = get_body("the Morning Lantern")  # period 8, window 5
    assert body_up(morning, 1) is True
    assert body_up(morning, 6) is False  # (6-1) % 8 == 5, outside the window
    assert body_up(morning, 0) is False  # before the calendar starts


def test_bodies_up_are_sorted_and_windowed():
    up = bodies_up(1)
    assert [b.name for b in up] == sorted(b.name for b in up)
    assert set(up) == set(CATALOGUE)  # every body is up on day 1 (all offsets 0)


def test_observable_bodies_gate_on_magnitude():
    naked = naked_eye_bodies(1)
    assert all(b.magnitude <= NAKED_EYE_LIMIT for b in naked)
    assert "the Morning Lantern" in {b.name for b in naked}
    assert "the Pale Wayfarer" not in {b.name for b in naked}  # magnitude 10.5, too faint
    # A deep instrument reaches the faint comets a naked eye cannot.
    deep = observable_bodies(1, reach=12.0)
    assert "the Pale Wayfarer" in {b.name for b in deep}
    assert len(deep) >= len(naked)


def test_component_contributes_no_prompt_of_its_own():
    # The marker never speaks for itself; the sky fragment names the wanderers instead.
    assert CelestialBodyComponent(name="x").prompt_fragments(None) == ()


# -- ensure_bodies (entities) -----------------------------------------------------------


def test_ensure_bodies_spawns_the_catalogue_once():
    actor = WorldActor()
    first = ensure_bodies(actor.world)
    assert set(first) == {b.name for b in CATALOGUE}
    spawned = list(actor.world.query().with_all([CelestialBodyComponent]).execute_entities())
    assert len(spawned) == len(CATALOGUE)

    second = ensure_bodies(actor.world)  # idempotent: reuse, never duplicate
    assert {name: e.id for name, e in first.items()} == {n: e.id for n, e in second.items()}
    assert len(list(actor.world.query().with_all([CelestialBodyComponent]).execute_entities())) == (
        len(CATALOGUE)
    )


# -- sky_bodies_fragments ---------------------------------------------------------------


def test_fragment_names_naked_eye_wanderers_on_a_clear_night():
    actor, character = _outdoor_world(day=1)
    lines = sky_bodies_fragments(actor.world, character)
    assert lines
    assert "the Morning Lantern" in lines[0]


def test_fragment_empty_indoors():
    actor, character = _outdoor_world(day=1, indoor=True)
    assert sky_bodies_fragments(actor.world, character) == []


def test_fragment_empty_for_no_character():
    actor, _character = _outdoor_world(day=1)
    assert sky_bodies_fragments(actor.world, None) == []


def test_fragment_empty_when_no_wanderers_are_up():
    # Day 46: (45 % 8 == 5) and (45 % 12 == 9) put both bright planets below the horizon.
    assert naked_eye_bodies(46) == ()
    actor, character = _outdoor_world(day=46, condition="clear")
    assert sky_bodies_fragments(actor.world, character) == []
