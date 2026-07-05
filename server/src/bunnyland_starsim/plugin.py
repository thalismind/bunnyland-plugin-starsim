"""Bunnyland plugin entrypoint for the out-of-tree starsim astronomy pack."""

from __future__ import annotations

from bunnyland.plugins import (
    CommandContribution,
    ContentContribution,
    DependencyContribution,
    EcsContribution,
    Plugin,
    RuntimeContribution,
)

from .bodies import CelestialBodyComponent, sky_bodies_fragments
from .celestial import CELESTIAL_ACTION_DEFINITIONS, CELESTIAL_ACTION_HANDLERS
from .components import (
    ConstellationLogComponent,
    SkyComponent,
    TelescopeComponent,
    WishLogComponent,
)
from .constellations import constellation_fragments
from .enrichment import StarsimWorldgenHook
from .events import (
    BodySightedEvent,
    BodyTrackedEvent,
    CelestialEventBeganEvent,
    ConstellationIdentifiedEvent,
    SkyChangedEvent,
    StargazedEvent,
    WishMadeEvent,
)
from .install import install_starsim
from .navigation import navigation_fragments
from .sky import sky_fragments
from .stargaze import STARGAZE_ACTION_DEFINITIONS, STARGAZE_ACTION_HANDLERS
from .starnav import star_compass_fragments
from .tracking import (
    TRACK_ACTION_DEFINITIONS,
    TRACK_ACTION_HANDLERS,
    TracksBody,
    tracking_fragments,
)

PLUGIN_ID = "bunnyland.starsim"

#: Optional synergy partners: starsim runs standalone, but interlocks when these are loaded.
STORYTELLER = "bunnyland.storyteller"
FESTIVALSIM = "bunnyland.festivalsim"
CARTOGRAPHYSIM = "bunnyland.cartographysim"


def plugin() -> Plugin:
    return Plugin(
        id=PLUGIN_ID,
        name="Bunnyland Starsim",
        version="0.2.0",
        default_enabled=True,
        dependencies=DependencyContribution(
            recommends=(STORYTELLER, FESTIVALSIM, CARTOGRAPHYSIM),
        ),
        ecs=EcsContribution(
            components=(
                SkyComponent,
                TelescopeComponent,
                ConstellationLogComponent,
                WishLogComponent,
                CelestialBodyComponent,
            ),
            edges=(TracksBody,),
        ),
        commands=CommandContribution(
            action_handlers=(
                STARGAZE_ACTION_HANDLERS
                + CELESTIAL_ACTION_HANDLERS
                + TRACK_ACTION_HANDLERS
            ),
            action_definitions=(
                STARGAZE_ACTION_DEFINITIONS
                + CELESTIAL_ACTION_DEFINITIONS
                + TRACK_ACTION_DEFINITIONS
            ),
            typed_events=(
                StargazedEvent,
                ConstellationIdentifiedEvent,
                WishMadeEvent,
                SkyChangedEvent,
                BodyTrackedEvent,
                BodySightedEvent,
                CelestialEventBeganEvent,
            ),
        ),
        runtime=RuntimeContribution(
            service_factories=(install_starsim,),
        ),
        content=ContentContribution(
            prompt_fragments=(
                sky_fragments,
                navigation_fragments,
                constellation_fragments,
                sky_bodies_fragments,
                tracking_fragments,
                star_compass_fragments,
            ),
            worldgen_hooks=(StarsimWorldgenHook,),
        ),
    )


def bunnyland_plugins() -> list[Plugin]:
    return [plugin()]


__all__ = ["PLUGIN_ID", "bunnyland_plugins", "plugin"]
