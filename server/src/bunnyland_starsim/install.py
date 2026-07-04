"""Runtime wiring: register the night-sky consequence on a world actor."""

from __future__ import annotations

from bunnyland.core.world_actor import WorldActor

from .sky import NightSkyConsequence


def install_starsim(actor: WorldActor) -> None:
    """Register the per-tick night-sky consequence (a ``service_factories`` entry)."""
    actor.register_consequence(NightSkyConsequence())


__all__ = ["install_starsim"]
