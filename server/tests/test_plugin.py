from __future__ import annotations

from bunnyland.core.world_actor import WorldActor
from bunnyland.plugins import apply_plugins, load_modules

from bunnyland_starsim import (
    CelestialBodyComponent,
    ConstellationLogComponent,
    SkyComponent,
    StarsimWorldgenHook,
    TelescopeComponent,
    TracksBody,
    WishLogComponent,
    constellation_fragments,
    navigation_fragments,
    sky_bodies_fragments,
    sky_fragments,
    star_compass_fragments,
    tracking_fragments,
)
from bunnyland_starsim.events import (
    BodySightedEvent,
    BodyTrackedEvent,
    CelestialEventBeganEvent,
)
from bunnyland_starsim.plugin import CARTOGRAPHYSIM, FESTIVALSIM, PLUGIN_ID, STORYTELLER


def test_plugin_loads_with_dotted_id():
    plugins = load_modules(["bunnyland_starsim"])
    # A dotted id is not module-qualified by the loader; it loads verbatim.
    assert PLUGIN_ID == "bunnyland.starsim"
    assert [p.id for p in plugins] == ["bunnyland.starsim"]


def test_plugin_declares_its_components():
    plugin = load_modules(["bunnyland_starsim"])[0]
    for component in (
        SkyComponent,
        TelescopeComponent,
        ConstellationLogComponent,
        WishLogComponent,
        CelestialBodyComponent,
    ):
        assert component in plugin.ecs.components


def test_plugin_declares_the_tracks_body_edge():
    plugin = load_modules(["bunnyland_starsim"])[0]
    assert TracksBody in plugin.ecs.edges


def test_plugin_declares_its_fragments():
    plugin = load_modules(["bunnyland_starsim"])[0]
    for fragment in (
        sky_fragments,
        navigation_fragments,
        constellation_fragments,
        sky_bodies_fragments,
        tracking_fragments,
        star_compass_fragments,
    ):
        assert fragment in plugin.content.prompt_fragments


def test_plugin_declares_its_v2_events():
    plugin = load_modules(["bunnyland_starsim"])[0]
    for event in (BodyTrackedEvent, BodySightedEvent, CelestialEventBeganEvent):
        assert event in plugin.commands.typed_events


def test_plugin_recommends_optional_synergy_partners():
    plugin = load_modules(["bunnyland_starsim"])[0]
    recommends = plugin.dependencies.recommends
    assert STORYTELLER in recommends
    assert FESTIVALSIM in recommends
    assert CARTOGRAPHYSIM in recommends


def test_plugin_declares_worldgen_hook():
    plugin = load_modules(["bunnyland_starsim"])[0]
    assert StarsimWorldgenHook in plugin.content.worldgen_hooks


def test_plugin_version():
    plugin = load_modules(["bunnyland_starsim"])[0]
    assert plugin.version == "0.2.0"


def test_plugin_applies_and_registers_verbs():
    actor = WorldActor()
    applied = apply_plugins(load_modules(["bunnyland_starsim"]), actor)
    assert applied[0].id == "bunnyland.starsim"
    command_types = {definition.command_type for definition in actor.action_definitions()}
    assert {"stargaze", "make-a-wish", "track-body"} <= command_types
