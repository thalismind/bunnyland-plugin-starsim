from __future__ import annotations

from bunnyland.core.world_actor import WorldActor
from bunnyland.plugins import apply_plugins, load_modules

from bunnyland_starsim import (
    ConstellationLogComponent,
    SkyComponent,
    StarsimWorldgenHook,
    TelescopeComponent,
    WishLogComponent,
    constellation_fragments,
    navigation_fragments,
    sky_fragments,
)
from bunnyland_starsim.plugin import PLUGIN_ID


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
    ):
        assert component in plugin.ecs.components


def test_plugin_declares_its_fragments():
    plugin = load_modules(["bunnyland_starsim"])[0]
    for fragment in (sky_fragments, navigation_fragments, constellation_fragments):
        assert fragment in plugin.content.prompt_fragments


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
    assert {"stargaze", "make-a-wish"} <= command_types
