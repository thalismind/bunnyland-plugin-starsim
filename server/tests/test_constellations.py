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

from bunnyland_starsim import (
    CATALOGUE,
    POLE_STAR,
    ConstellationLogComponent,
    constellation_fragments,
    constellations_up,
    is_known_constellation,
    record_identified,
)


def _character(actor):
    room = spawn_entity(actor.world, [RoomComponent(title="Field")])
    character = spawn_entity(
        actor.world, [IdentityComponent(name="Vin", kind="character"), CharacterComponent()]
    )
    room.add_relationship(Contains(mode=ContainmentMode.ROOM_CONTENT), character.id)
    return character


# -- catalogue --------------------------------------------------------------------------


def test_pole_star_is_circumpolar_and_always_up():
    for season in ("spring", "summer", "autumn", "winter"):
        assert POLE_STAR in constellations_up(season)


def test_seasonal_constellations_only_appear_in_season():
    spring = constellations_up("spring")
    assert "the Hare" in spring
    assert "the Kiln" not in spring  # summer figure
    assert "the Kiln" in constellations_up("summer")


def test_constellations_up_is_sorted():
    up = constellations_up("winter")
    assert list(up) == sorted(up)


def test_is_known_constellation():
    assert is_known_constellation("the Hare") is True
    assert is_known_constellation("the Toaster") is False


def test_catalogue_names_are_unique():
    names = [c.name for c in CATALOGUE]
    assert len(names) == len(set(names))


# -- logging ----------------------------------------------------------------------------


def test_record_identified_creates_the_log():
    actor = WorldActor()
    character = _character(actor)
    assert record_identified(character, "the Hare") is True
    assert character.get_component(ConstellationLogComponent).identified == ("the Hare",)


def test_record_identified_is_idempotent():
    actor = WorldActor()
    character = _character(actor)
    record_identified(character, "the Hare")
    assert record_identified(character, "the Hare") is False
    assert character.get_component(ConstellationLogComponent).identified == ("the Hare",)


def test_record_identified_keeps_the_log_sorted():
    actor = WorldActor()
    character = _character(actor)
    record_identified(character, "the Lantern")
    record_identified(character, "the Hare")
    identified = character.get_component(ConstellationLogComponent).identified
    assert list(identified) == sorted(identified)


# -- fragments --------------------------------------------------------------------------


def test_fragment_lists_charted_constellations():
    actor = WorldActor()
    character = _character(actor)
    record_identified(character, "the Hare")
    record_identified(character, "the Lantern")
    lines = constellation_fragments(actor.world, character)
    assert len(lines) == 1
    assert "the Hare" in lines[0]
    assert "the Lantern" in lines[0]
    assert "2 constellations" in lines[0]


def test_fragment_empty_without_a_log():
    actor = WorldActor()
    character = _character(actor)
    assert constellation_fragments(actor.world, character) == []


def test_fragment_empty_for_no_character():
    actor = WorldActor()
    assert constellation_fragments(actor.world, None) == []
