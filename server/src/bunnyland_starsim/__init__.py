"""Out-of-tree Bunnyland plugin: a stargazing and astronomy pack.

Mechanics:
- **The turning sky** — a :class:`~bunnyland_starsim.sky.NightSkyConsequence` derives the
  visible sky (:class:`~bunnyland_starsim.components.SkyComponent`) from the world clock:
  stars are out only at night, under clear skies, in outdoor rooms.
- **Stargaze** — the ``stargaze`` verb reports the sky, lifts the gazer's mood, and can
  chart a constellation.
- **Constellations** — a seasonal + circumpolar catalogue, logged per character.
- **Celestial events** — deterministic meteor showers and comets, with a ``make-a-wish`` verb.
- **Navigation by stars** — the pole star fixes due north when the stars are visible.
"""

from .affect import lift_mood
from .celestial import (
    CELESTIAL_ACTION_DEFINITIONS,
    CELESTIAL_ACTION_HANDLERS,
    COMET,
    METEOR_SHOWER,
    WISH_EVENTS,
    MakeAWishHandler,
    celestial_event_for,
)
from .components import (
    ConstellationLogComponent,
    SkyComponent,
    TelescopeComponent,
    WishLogComponent,
)
from .constellations import (
    CATALOGUE,
    POLE_STAR,
    Constellation,
    constellation_fragments,
    constellations_up,
    is_known_constellation,
    record_identified,
)
from .events import (
    ConstellationIdentifiedEvent,
    SkyChangedEvent,
    StargazedEvent,
    WishMadeEvent,
)
from .install import install_starsim
from .navigation import navigation_fragments
from .plugin import PLUGIN_ID, bunnyland_plugins, plugin
from .prefabs import spawn_telescope
from .sky import (
    NightSkyConsequence,
    derive_sky,
    sky_fragments,
    stars_visible_from_room,
)
from .spatial import holder_of, room_of
from .stargaze import (
    STARGAZE_ACTION_DEFINITIONS,
    STARGAZE_ACTION_HANDLERS,
    StargazeHandler,
)

__all__ = [
    "CATALOGUE",
    "CELESTIAL_ACTION_DEFINITIONS",
    "CELESTIAL_ACTION_HANDLERS",
    "COMET",
    "METEOR_SHOWER",
    "PLUGIN_ID",
    "POLE_STAR",
    "STARGAZE_ACTION_DEFINITIONS",
    "STARGAZE_ACTION_HANDLERS",
    "WISH_EVENTS",
    "Constellation",
    "ConstellationIdentifiedEvent",
    "ConstellationLogComponent",
    "MakeAWishHandler",
    "NightSkyConsequence",
    "SkyChangedEvent",
    "SkyComponent",
    "StargazeHandler",
    "StargazedEvent",
    "TelescopeComponent",
    "WishLogComponent",
    "WishMadeEvent",
    "bunnyland_plugins",
    "celestial_event_for",
    "constellation_fragments",
    "constellations_up",
    "derive_sky",
    "holder_of",
    "install_starsim",
    "is_known_constellation",
    "lift_mood",
    "navigation_fragments",
    "plugin",
    "record_identified",
    "room_of",
    "sky_fragments",
    "spawn_telescope",
    "stars_visible_from_room",
]
