"""Bunnyland plugin entrypoint for the out-of-tree starsim astronomy pack."""

from __future__ import annotations

from bunnyland.plugins import (
    CommandContribution,
    ContentContribution,
    EcsContribution,
    Plugin,
    RuntimeContribution,
)

from .celestial import CELESTIAL_ACTION_DEFINITIONS, CELESTIAL_ACTION_HANDLERS
from .components import (
    ConstellationLogComponent,
    SkyComponent,
    TelescopeComponent,
    WishLogComponent,
)
from .constellations import constellation_fragments
from .events import (
    ConstellationIdentifiedEvent,
    SkyChangedEvent,
    StargazedEvent,
    WishMadeEvent,
)
from .install import install_starsim
from .navigation import navigation_fragments
from .sky import sky_fragments
from .stargaze import STARGAZE_ACTION_DEFINITIONS, STARGAZE_ACTION_HANDLERS

PLUGIN_ID = "bunnyland.starsim"


def plugin() -> Plugin:
    return Plugin(
        id=PLUGIN_ID,
        name="Bunnyland Starsim",
        version="0.1.0",
        default_enabled=True,
        ecs=EcsContribution(
            components=(
                SkyComponent,
                TelescopeComponent,
                ConstellationLogComponent,
                WishLogComponent,
            ),
        ),
        commands=CommandContribution(
            action_handlers=STARGAZE_ACTION_HANDLERS + CELESTIAL_ACTION_HANDLERS,
            action_definitions=STARGAZE_ACTION_DEFINITIONS + CELESTIAL_ACTION_DEFINITIONS,
            typed_events=(
                StargazedEvent,
                ConstellationIdentifiedEvent,
                WishMadeEvent,
                SkyChangedEvent,
            ),
        ),
        runtime=RuntimeContribution(
            service_factories=(install_starsim,),
        ),
        content=ContentContribution(
            prompt_fragments=(sky_fragments, navigation_fragments, constellation_fragments),
        ),
    )


def bunnyland_plugins() -> list[Plugin]:
    return [plugin()]


__all__ = ["PLUGIN_ID", "bunnyland_plugins", "plugin"]
