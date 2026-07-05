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

v2 mechanics:
- **Planets & comets tracking** — a moving catalogue of wanderers, each up on a deterministic
  cycle; the ``track-body`` verb charts one as a typed :class:`TracksBody` edge.
- **Telescope tiers** — a telescope's ``power`` reads as a tier reaching a fainter limiting
  magnitude, gating fainter planets and comets behind the instrument needed to see them.
- **Celestial incidents** — a comet or meteor shower is mirrored onto the shared storyteller
  incident surface and published for a festival to turn into a spectacle.
"""

from .affect import lift_mood
from .bodies import (
    CATALOGUE as BODY_CATALOGUE,
)
from .bodies import (
    CelestialBody,
    CelestialBodyComponent,
    bodies_up,
    body_up,
    ensure_bodies,
    is_known_body,
    observable_bodies,
    sky_bodies_fragments,
)
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
from .incident import CelestialIncidentConsequence
from .install import install_starsim
from .navigation import navigation_fragments
from .plugin import PLUGIN_ID, bunnyland_plugins, plugin
from .prefabs import spawn_telescope, spawn_tiered_telescope
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
from .starnav import star_compass_fragments
from .telescopes import (
    TELESCOPE_TIERS,
    reach_magnitude,
    tier_for_power,
    tier_name,
)
from .tracking import (
    TRACK_ACTION_DEFINITIONS,
    TRACK_ACTION_HANDLERS,
    TrackBodyHandler,
    TracksBody,
    tracking_fragments,
)

__all__ = [
    "BODY_CATALOGUE",
    "CATALOGUE",
    "CELESTIAL_ACTION_DEFINITIONS",
    "CELESTIAL_ACTION_HANDLERS",
    "COMET",
    "METEOR_SHOWER",
    "PLUGIN_ID",
    "POLE_STAR",
    "STARGAZE_ACTION_DEFINITIONS",
    "STARGAZE_ACTION_HANDLERS",
    "TELESCOPE_TIERS",
    "TRACK_ACTION_DEFINITIONS",
    "TRACK_ACTION_HANDLERS",
    "WISH_EVENTS",
    "BodySightedEvent",
    "BodyTrackedEvent",
    "CelestialBody",
    "CelestialBodyComponent",
    "CelestialEventBeganEvent",
    "CelestialIncidentConsequence",
    "Constellation",
    "ConstellationIdentifiedEvent",
    "ConstellationLogComponent",
    "MakeAWishHandler",
    "NightSkyConsequence",
    "SkyChangedEvent",
    "SkyComponent",
    "StargazeHandler",
    "StargazedEvent",
    "StarsimWorldgenHook",
    "TelescopeComponent",
    "TrackBodyHandler",
    "TracksBody",
    "WishLogComponent",
    "WishMadeEvent",
    "bodies_up",
    "body_up",
    "bunnyland_plugins",
    "celestial_event_for",
    "constellation_fragments",
    "constellations_up",
    "derive_sky",
    "ensure_bodies",
    "holder_of",
    "install_starsim",
    "is_known_body",
    "is_known_constellation",
    "lift_mood",
    "navigation_fragments",
    "observable_bodies",
    "plugin",
    "reach_magnitude",
    "record_identified",
    "room_of",
    "sky_bodies_fragments",
    "sky_fragments",
    "spawn_telescope",
    "spawn_tiered_telescope",
    "star_compass_fragments",
    "stars_visible_from_room",
    "tier_for_power",
    "tier_name",
    "tracking_fragments",
]
