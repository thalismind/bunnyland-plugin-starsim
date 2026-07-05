"""A comet or meteor shower as a shared storyteller incident.

The sky's celestial events are calendar-driven (see :mod:`~bunnyland_starsim.celestial`), but a
comet or meteor shower is also something *everyone experiences at once* — exactly what the core
storyteller layer exists to pace. This consequence mirrors the overhead event onto a core
:class:`~bunnyland.mechanics.storyteller.IncidentComponent` entity: it **opens** an incident
when a comet or shower begins and **resolves** it when the sky goes quiet, so the celestial
event shows up on the same world-incident surface as every other pack's incidents.

On opening it also publishes a world-visible
:class:`~bunnyland_starsim.events.CelestialEventBeganEvent` — the connector surface a festival
pack can subscribe to in order to throw a matching spectacle. Nothing here reaches into another
pack; it only reuses core types and emits a public event.

Everything stays deterministic: the incident's existence is a pure function of the calendar
sky, never of randomness or wall-clock time.
"""

from __future__ import annotations

from dataclasses import replace

from bunnyland.core import IdentityComponent, spawn_entity
from bunnyland.core.ecs import replace_component
from bunnyland.core.events import DomainEvent, EventVisibility, event_base
from bunnyland.mechanics.storyteller import (
    IncidentComponent,
    IncidentResolvedEvent,
    IncidentStartedEvent,
)
from relics import Entity, World

from .celestial import COMET, METEOR_SHOWER
from .events import CelestialEventBeganEvent
from .sky import derive_sky

#: Overhead celestial event -> the storyteller incident kind it opens.
CELESTIAL_INCIDENT_KINDS: dict[str, str] = {
    METEOR_SHOWER: "meteor_shower",
    COMET: "comet",
}


def _active_celestial_incident(world: World) -> Entity | None:
    """The unresolved celestial incident entity currently open, or ``None``."""
    kinds = set(CELESTIAL_INCIDENT_KINDS.values())
    for entity in world.query().with_all([IncidentComponent]).execute_entities():
        incident = entity.get_component(IncidentComponent)
        if incident.kind in kinds and incident.resolved_at_epoch is None:
            return entity
    return None


class CelestialIncidentConsequence:
    """Open and resolve a storyteller incident tracking the overhead celestial event."""

    def process(self, world: World, epoch: int) -> list[DomainEvent]:
        sky = derive_sky(world)
        if sky is None:
            return []
        desired_kind = CELESTIAL_INCIDENT_KINDS.get(sky.event, "")
        active = _active_celestial_incident(world)
        active_kind = active.get_component(IncidentComponent).kind if active is not None else ""
        if active_kind == desired_kind:
            return []

        events: list[DomainEvent] = []
        if active is not None:
            incident = active.get_component(IncidentComponent)
            replace_component(active, replace(incident, resolved_at_epoch=epoch))
            events.append(
                IncidentResolvedEvent(
                    **event_base(
                        epoch,
                        default_visibility=EventVisibility.PUBLIC,
                        actor_id=str(active.id),
                        incident_id=str(active.id),
                        kind=incident.kind,
                    )
                )
            )
        if desired_kind:
            incident_entity = spawn_entity(
                world,
                [
                    IdentityComponent(name=sky.event, kind="incident", tags=("starsim",)),
                    IncidentComponent(
                        kind=desired_kind,
                        budget_spent=0.0,
                        started_at_epoch=epoch,
                    ),
                ],
            )
            events.append(
                IncidentStartedEvent(
                    **event_base(
                        epoch,
                        default_visibility=EventVisibility.PUBLIC,
                        actor_id=str(incident_entity.id),
                        incident_id=str(incident_entity.id),
                        kind=desired_kind,
                    )
                )
            )
            events.append(
                CelestialEventBeganEvent(
                    **event_base(
                        epoch,
                        default_visibility=EventVisibility.PUBLIC,
                        celestial_event=sky.event,
                        incident_id=str(incident_entity.id),
                        spectacle=desired_kind,
                    )
                )
            )
        return events


__all__ = [
    "CELESTIAL_INCIDENT_KINDS",
    "CelestialIncidentConsequence",
]
