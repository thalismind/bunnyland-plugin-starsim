"""Runtime wiring: register the night-sky consequence on a world actor."""

from __future__ import annotations

from bunnyland.core.world_actor import WorldActor

from .incident import CelestialIncidentConsequence
from .sky import NightSkyConsequence


def install_starsim(actor: WorldActor) -> None:
    """Register the per-tick starsim consequences (a ``service_factories`` entry).

    - :class:`~bunnyland_starsim.sky.NightSkyConsequence` derives the sky each tick.
    - :class:`~bunnyland_starsim.incident.CelestialIncidentConsequence` mirrors a comet or
      meteor shower onto the shared storyteller incident surface.
    """
    actor.register_consequence(NightSkyConsequence())
    actor.register_consequence(CelestialIncidentConsequence())


__all__ = ["install_starsim"]
