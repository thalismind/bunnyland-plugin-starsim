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
from bunnyland.prompts.context import ComponentPromptContext, PromptPerspective

from bunnyland_starsim import spawn_telescope
from bunnyland_starsim.bodies import ensure_bodies
from bunnyland_starsim.events import BodySightedEvent, BodyTrackedEvent
from bunnyland_starsim.tracking import (
    TrackBodyHandler,
    TracksBody,
    record_tracking,
    tracking_fragments,
)

SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR
NIGHT = 2 * SECONDS_PER_HOUR
DAY = 12 * SECONDS_PER_HOUR


def _world(*, indoor=False, seconds=None, condition=None):
    actor = WorldActor()
    clock = list(actor.world.query().with_all([WorldClockComponent]).execute_entities())[0]
    if seconds is not None:
        replace_component(clock, WorldClockComponent(game_time_seconds=seconds))
    if condition is not None:
        clock.add_component(WeatherComponent(condition=condition))
    room = spawn_entity(actor.world, [RoomComponent(title="Hill", indoor=indoor)])
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
        command_type="track-body",
        cost=CommandCost(action=1),
        lane=Lane.WORLD,
        payload=payload or {},
    )


def _ctx(actor, epoch=0):
    return HandlerContext(world=actor.world, epoch=epoch)


def _track(actor, character, body, *, epoch=0):
    return TrackBodyHandler().execute(_ctx(actor, epoch), _cmd(character.id, {"body": body}))


# -- happy paths ------------------------------------------------------------------------


def test_track_a_bright_planet_naked_eye():
    actor, room, character = _world()  # default clear night, day 1
    result = _track(actor, character, "the Red Wanderer")
    assert result.ok
    tracked = next(e for e in result.events if isinstance(e, BodyTrackedEvent))
    assert tracked.body == "the Red Wanderer"
    assert tracked.instrument == "naked eye"
    assert tracked.sightings == 1
    # A first sighting also announces a BodySightedEvent.
    assert any(isinstance(e, BodySightedEvent) for e in result.events)
    # A typed edge now records the observation.
    edges = list(character.get_relationships(TracksBody))
    assert len(edges) == 1


def test_track_lifts_mood():
    actor, _room, character = _world()
    TrackBodyHandler().execute(_ctx(actor), _cmd(character.id, {"body": "the Red Wanderer"}))
    thoughts = list(actor.world.query().with_all([ThoughtComponent]).execute_entities())
    assert thoughts
    assert thoughts[0].get_component(ThoughtComponent).affect_delta.curiosity > 0


def test_repeat_sighting_increments_without_a_new_sighted_event():
    actor, _room, character = _world()
    handler = TrackBodyHandler()
    handler.execute(_ctx(actor, epoch=0), _cmd(character.id, {"body": "the Red Wanderer"}))
    second = handler.execute(
        _ctx(actor, epoch=10), _cmd(character.id, {"body": "the Red Wanderer"})
    )
    assert second.ok
    tracked = next(e for e in second.events if isinstance(e, BodyTrackedEvent))
    assert tracked.sightings == 2
    assert not any(isinstance(e, BodySightedEvent) for e in second.events)
    assert len(list(character.get_relationships(TracksBody))) == 1  # no duplicate edge


def test_a_telescope_reaches_a_faint_comet_and_deepens_wonder():
    plain_actor, _r1, plain = _world()
    scope_actor, _r2, gazer = _world()
    _hold(gazer, spawn_telescope(scope_actor.world, power=3.0))  # great observatory, mag 12

    # The faint Pale Wayfarer (mag 10.5) is out of naked-eye reach...
    naked = TrackBodyHandler().execute(
        _ctx(plain_actor), _cmd(plain.id, {"body": "the Pale Wayfarer"})
    )
    assert not naked.ok
    # ...but the great observatory brings it in.
    scoped = TrackBodyHandler().execute(
        _ctx(scope_actor), _cmd(gazer.id, {"body": "the Pale Wayfarer"})
    )
    assert scoped.ok
    tracked = next(e for e in scoped.events if isinstance(e, BodyTrackedEvent))
    assert tracked.instrument == "great observatory"


def test_tracking_two_different_bodies_keeps_two_edges():
    actor, _room, character = _world()  # day 1: both bright planets are up
    handler = TrackBodyHandler()
    handler.execute(_ctx(actor), _cmd(character.id, {"body": "the Red Wanderer"}))
    second = handler.execute(_ctx(actor), _cmd(character.id, {"body": "the Morning Lantern"}))
    assert second.ok
    assert any(isinstance(e, BodySightedEvent) for e in second.events)  # a fresh sighting
    assert len(list(character.get_relationships(TracksBody))) == 2


def test_rejects_when_the_sky_cannot_be_derived():
    actor, _room, character = _world()
    for clock in list(actor.world.query().with_all([WorldClockComponent]).execute_entities()):
        actor.world.remove(clock.id)
    result = _track(actor, character, "the Red Wanderer")
    assert not result.ok
    assert result.reason == "there is no sky overhead"


def test_record_tracking_advances_the_edge_in_place():
    actor, _room, character = _world()
    body = ensure_bodies(actor.world)["the Red Wanderer"]
    n1, new1 = record_tracking(character, body, epoch=1)
    n2, new2 = record_tracking(character, body, epoch=5)
    assert (n1, new1) == (1, True)
    assert (n2, new2) == (2, False)
    edge, _target = next(iter(character.get_relationships(TracksBody)))
    assert edge.sightings == 2
    assert edge.first_epoch == 1 and edge.last_epoch == 5


# -- rejections -------------------------------------------------------------------------


def test_rejects_invalid_character_id():
    actor, _room, _character = _world()
    result = TrackBodyHandler().execute(_ctx(actor), _cmd("???", {"body": "the Red Wanderer"}))
    assert not result.ok
    assert result.reason == "invalid character id"


def test_rejects_character_with_no_room():
    actor = WorldActor()
    drifter = spawn_entity(
        actor.world, [IdentityComponent(name="drifter", kind="character"), CharacterComponent()]
    )
    result = TrackBodyHandler().execute(_ctx(actor), _cmd(drifter.id, {"body": "the Red Wanderer"}))
    assert not result.ok
    assert result.reason == "you are not in a room"


def test_rejects_indoors():
    actor, _room, character = _world(indoor=True)
    result = _track(actor, character, "the Red Wanderer")
    assert not result.ok
    assert result.reason == "you are indoors; you cannot see the sky"


def test_rejects_in_daylight():
    actor, _room, character = _world(seconds=DAY)
    result = _track(actor, character, "the Red Wanderer")
    assert not result.ok
    assert result.reason == "the stars are not out"


def test_rejects_under_clouds():
    actor, _room, character = _world(condition="cloudy")
    result = _track(actor, character, "the Red Wanderer")
    assert not result.ok
    assert result.reason == "clouds hide the stars"


def test_rejects_empty_body_name():
    actor, _room, character = _world()
    result = TrackBodyHandler().execute(_ctx(actor), _cmd(character.id, {"body": "  "}))
    assert not result.ok
    assert result.reason == "name a planet or comet to track"


def test_rejects_unknown_body():
    actor, _room, character = _world()
    result = TrackBodyHandler().execute(_ctx(actor), _cmd(character.id, {"body": "the Moon Base"}))
    assert not result.ok
    assert result.reason == "the sky charts list no such body"


def test_rejects_body_below_the_horizon():
    # Day 6: the Morning Lantern (period 8, window 5) has set.
    actor, _room, character = _world(seconds=(6 - 1) * SECONDS_PER_DAY + NIGHT, condition="clear")
    result = TrackBodyHandler().execute(
        _ctx(actor), _cmd(character.id, {"body": "the Morning Lantern"})
    )
    assert not result.ok
    assert result.reason == "that body is not above the horizon tonight"


def test_rejects_faint_body_beyond_naked_eye():
    actor, _room, character = _world()
    result = _track(actor, character, "the Pale Wayfarer")
    assert not result.ok
    assert result.reason == "it is too faint to make out; you need a stronger telescope"


# -- fragments --------------------------------------------------------------------------


def test_tracking_fragment_lists_charted_wanderers():
    actor, _room, character = _world()  # for_entity defaults to a first-person view
    TrackBodyHandler().execute(_ctx(actor), _cmd(character.id, {"body": "the Red Wanderer"}))
    lines = tracking_fragments(actor.world, character)
    assert lines
    assert "the Red Wanderer" in lines[0]
    assert "tracking 1" in lines[0]


def test_tracking_fragment_empty_without_any_edges():
    actor, _room, character = _world()
    assert tracking_fragments(actor.world, character) == []


def test_tracking_fragment_empty_for_no_character():
    actor, _room, _character = _world()
    assert tracking_fragments(actor.world, None) == []


def test_tracking_fragment_empty_in_third_person(monkeypatch):
    actor, _room, character = _world()
    TrackBodyHandler().execute(_ctx(actor), _cmd(character.id, {"body": "the Red Wanderer"}))
    onlooker = spawn_entity(
        actor.world, [IdentityComponent(name="Onlooker", kind="character"), CharacterComponent()]
    )
    original = ComponentPromptContext.for_entity

    def as_onlooker(world, entity, **kwargs):
        return original(world, entity, perspective=PromptPerspective(viewer=onlooker))

    monkeypatch.setattr(ComponentPromptContext, "for_entity", staticmethod(as_onlooker))
    assert tracking_fragments(actor.world, character) == []


def test_tracking_fragment_skips_a_removed_body():
    actor, _room, character = _world()
    TrackBodyHandler().execute(_ctx(actor), _cmd(character.id, {"body": "the Red Wanderer"}))
    # Remove the body entity: its edge lingers but the fragment skips a dead target.
    for _edge, target_id in list(character.get_relationships(TracksBody)):
        actor.world.remove(target_id)
    assert tracking_fragments(actor.world, character) == []
