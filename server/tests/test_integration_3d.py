from __future__ import annotations

from bunnyland.core import RoomComponent, WorldActor, WorldClockComponent, spawn_entity
from bunnyland.core.ecs import replace_component
from bunnyland.foundation.environment.mechanics import WeatherComponent
from bunnyland.foundation.media.plugin import plugin as media_plugin
from bunnyland.plugins import apply_plugins

from bunnyland_starsim.plugin import plugin as starsim_plugin


def _actor(tmp_path, monkeypatch):
    from bunnyland_3d.plugin import plugin as plugin_3d

    monkeypatch.setenv("BUNNYLAND_MEDIA_DIR", str(tmp_path / "media"))
    actor = WorldActor()
    apply_plugins([media_plugin(), plugin_3d(), starsim_plugin()], actor)
    return actor


def _clock(actor):
    return next(iter(actor.world.query().with_all([WorldClockComponent]).execute_entities()))


def test_clear_night_projects_starfield_only_outdoors(tmp_path, monkeypatch):
    from bunnyland_3d.api import room_scene_view

    actor = _actor(tmp_path, monkeypatch)
    outdoor = spawn_entity(actor.world, [RoomComponent(title="Hilltop")])
    indoor = spawn_entity(actor.world, [RoomComponent(title="Observatory Office", indoor=True)])

    assert (
        room_scene_view(actor, str(outdoor.id))["room"]["environment3d"]["skybox_preset"]
        == "bunnyland.starsim/clear-night"
    )
    assert room_scene_view(actor, str(indoor.id))["room"]["environment3d"] is None


def test_daylight_and_clouds_remove_starsim_skybox_dynamically(tmp_path, monkeypatch):
    from bunnyland_3d.api import room_scene_view

    actor = _actor(tmp_path, monkeypatch)
    room = spawn_entity(actor.world, [RoomComponent(title="Hilltop")])
    clock = _clock(actor)

    replace_component(clock, WorldClockComponent(game_time_seconds=12 * 60 * 60))
    assert room_scene_view(actor, str(room.id))["room"]["environment3d"] is None

    replace_component(clock, WorldClockComponent(game_time_seconds=0))
    clock.add_component(WeatherComponent(condition="cloudy"))
    assert room_scene_view(actor, str(room.id))["room"]["environment3d"] is None
