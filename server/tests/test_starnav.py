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
from pydantic.dataclasses import dataclass
from relics import Component

from bunnyland_starsim import POLE_STAR, star_compass_fragments, starnav

DAY = 12 * 3600


@dataclass(frozen=True)
class FakeCompass(Component):
    """Stand-in for a cartography pack's public CompassComponent."""

    bearing: str = "north"


def _world(*, indoor=False, seconds=None):
    actor = WorldActor()
    if seconds is not None:
        clock = list(actor.world.query().with_all([WorldClockComponent]).execute_entities())[0]
        replace_component(clock, WorldClockComponent(game_time_seconds=seconds))
    room = spawn_entity(actor.world, [RoomComponent(title="Ridge", indoor=indoor)])
    character = spawn_entity(actor.world, [IdentityComponent(name="Vin", kind="character")])
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return actor, character


def _hold(holder, item):
    holder.add_relationship(Contains(mode=ContainmentMode.INVENTORY), item.id)


def test_no_cartography_pack_means_no_corroboration():
    # In the standalone repo the conditional import leaves CompassComponent None.
    assert starnav.CompassComponent is None
    actor, character = _world()
    assert star_compass_fragments(actor.world, character) == []


def test_no_character_is_empty():
    actor, _character = _world()
    assert star_compass_fragments(actor.world, None) == []


def test_compass_in_hand_is_corroborated_by_the_pole_star(monkeypatch):
    monkeypatch.setattr(starnav, "CompassComponent", FakeCompass)
    actor, character = _world()
    compass = spawn_entity(
        actor.world, [IdentityComponent(name="compass", kind="item"), FakeCompass()]
    )
    _hold(character, compass)
    lines = star_compass_fragments(actor.world, character)
    assert len(lines) == 1
    assert POLE_STAR in lines[0]
    assert "compass" in lines[0]


def test_no_line_without_the_compass_even_when_the_pack_is_present(monkeypatch):
    monkeypatch.setattr(starnav, "CompassComponent", FakeCompass)
    actor, character = _world()
    # Carrying an unrelated item is not a compass; the pole star stays silent.
    _hold(character, spawn_entity(actor.world, [IdentityComponent(name="rock", kind="item")]))
    assert star_compass_fragments(actor.world, character) == []


def test_no_line_when_stars_are_hidden(monkeypatch):
    monkeypatch.setattr(starnav, "CompassComponent", FakeCompass)
    actor, character = _world(indoor=True)
    compass = spawn_entity(
        actor.world, [IdentityComponent(name="compass", kind="item"), FakeCompass()]
    )
    _hold(character, compass)
    assert star_compass_fragments(actor.world, character) == []
