"""The ``track-body`` verb: chart a planet or comet across the nights.

Tracking a wanderer is only possible where the stars are visible — outdoors, at night, under
a clear sky — *and* when the body is both above the horizon tonight and bright enough for the
telescope in hand (a faint planet or a comet needs a real instrument; see
:mod:`~bunnyland_starsim.telescopes`). A successful observation records a **typed
:class:`TracksBody` edge** from the gazer to the body's entity — one edge per (gazer, body),
carrying the sighting tally and first/last epoch — and lifts the gazer's mood with wonder,
deepened by the instrument. Every relationship here is a typed edge, never a list on a
component, so each edge type stays its own index.

Validation order follows the project convention: invalid id -> missing entity -> not in a
room -> cannot see the sky -> invalid argument -> not up -> too faint -> apply.
"""

from __future__ import annotations

from dataclasses import replace

from bunnyland.core import RoomComponent
from bunnyland.core.actions import ActionArgument, ActionDefinition
from bunnyland.core.commands import CommandCost, Lane, SubmittedCommand
from bunnyland.core.components import AffectDelta
from bunnyland.core.events import EventVisibility
from bunnyland.core.handlers import HandlerContext, HandlerResult, ok, rejected, require_character
from pydantic.dataclasses import dataclass
from relics import Edge, Entity, World

from .affect import lift_mood
from .bodies import CelestialBodyComponent, body_up, ensure_bodies, get_body, is_known_body
from .events import BodySightedEvent, BodyTrackedEvent
from .sky import derive_sky, stars_visible_from_room
from .spatial import room_of
from .telescopes import held_telescope, reach_magnitude, tier_name

#: Mood lift from charting a wanderer (curiosity + a little calm wonder).
TRACK_MOOD = AffectDelta(valence=3.0, stress=-2.0, curiosity=4.0)
#: Extra wonder the first time a body is ever sighted.
FIRST_SIGHTING_MOOD = AffectDelta(valence=4.0, curiosity=3.0)
#: Multiplier applied per unit of telescope power while an instrument is in hand.
TELESCOPE_BONUS = 1.5


@dataclass(frozen=True)
class TracksBody(Edge):
    """A gazer's observing record for one celestial body (directed, one per body)."""

    sightings: int = 0
    first_epoch: int = 0
    last_epoch: int = 0


def _scaled(delta: AffectDelta, factor: float) -> AffectDelta:
    return AffectDelta(
        valence=delta.valence * factor,
        stress=delta.stress * factor,
        confidence=delta.confidence * factor,
        curiosity=delta.curiosity * factor,
    )


def _sum(a: AffectDelta, b: AffectDelta) -> AffectDelta:
    return AffectDelta(
        valence=a.valence + b.valence,
        stress=a.stress + b.stress,
        confidence=a.confidence + b.confidence,
        curiosity=a.curiosity + b.curiosity,
    )


def _no_stars_reason(sky, room: Entity) -> str:
    if room.has_component(RoomComponent) and room.get_component(RoomComponent).indoor:
        return "you are indoors; you cannot see the sky"
    if sky.phase != "night":
        return "the stars are not out"
    return "clouds hide the stars"


def _existing_edge(character: Entity, body_id) -> TracksBody | None:
    for edge, target_id in character.get_relationships(TracksBody):
        if target_id == body_id:
            return edge
    return None


def record_tracking(character: Entity, body_entity: Entity, epoch: int) -> tuple[int, bool]:
    """Add or advance the ``TracksBody`` edge to ``body_entity``; return (sightings, is_new).

    ``add_relationship`` overwrites the existing edge of the same type and target, so a
    repeat sighting increments the tally in place rather than piling up duplicate edges.
    """
    current = _existing_edge(character, body_entity.id)
    is_new = current is None
    if current is None:
        updated = TracksBody(sightings=1, first_epoch=epoch, last_epoch=epoch)
    else:
        updated = replace(current, sightings=current.sightings + 1, last_epoch=epoch)
    character.add_relationship(updated, body_entity.id)
    return updated.sightings, is_new


class TrackBodyHandler:
    """Observe a named planet or comet and chart it as a typed edge."""

    command_type = "track-body"

    def execute(self, ctx: HandlerContext, command: SubmittedCommand) -> HandlerResult:
        character_id, character, rejection = require_character(ctx, command.character_id)
        if rejection is not None:
            return rejection
        room = room_of(ctx.world, character_id)
        if room is None:
            return rejected("you are not in a room")
        sky = derive_sky(ctx.world)
        if sky is None:
            return rejected("there is no sky overhead")
        if not stars_visible_from_room(sky, room):
            return rejected(_no_stars_reason(sky, room))

        name = (command.payload.get("body") or "").strip()
        if not name:
            return rejected("name a planet or comet to track")
        if not is_known_body(name):
            return rejected("the sky charts list no such body")
        body = get_body(name)
        if not body_up(body, sky.day):
            return rejected("that body is not above the horizon tonight")

        telescope = held_telescope(ctx.world, character)
        if body.magnitude > reach_magnitude(telescope):
            return rejected("it is too faint to make out; you need a stronger telescope")

        body_entity = ensure_bodies(ctx.world)[name]
        sightings, is_new = record_tracking(character, body_entity, ctx.epoch)

        mood = TRACK_MOOD
        if is_new:
            mood = _sum(mood, FIRST_SIGHTING_MOOD)
        if telescope is not None:
            mood = _scaled(mood, TELESCOPE_BONUS * telescope.power)
        lift_mood(
            ctx.world,
            character,
            mood,
            ctx.epoch,
            label="wonder",
            text=f"You have the {name} in your sights.",
        )

        events = [
            BodyTrackedEvent(
                **ctx.event_base(
                    visibility=EventVisibility.ROOM,
                    actor_id=str(character_id),
                    room_id=str(room.id),
                    body=name,
                    kind=body.kind,
                    sightings=sightings,
                    instrument=tier_name(telescope),
                )
            )
        ]
        if is_new:
            events.append(
                BodySightedEvent(
                    **ctx.event_base(
                        visibility=EventVisibility.ROOM,
                        actor_id=str(character_id),
                        room_id=str(room.id),
                        body=name,
                        kind=body.kind,
                    )
                )
            )
        return ok(*events)


def tracking_fragments(world: World, character: Entity) -> list[str]:
    """First-person line summarising the wanderers a character has charted."""
    if character is None:
        return []
    from bunnyland.prompts.context import ComponentPromptContext

    ctx = ComponentPromptContext.for_entity(world, character)
    if not ctx.is_first_person:
        return []
    names = []
    for _edge, target_id in character.get_relationships(TracksBody):
        if not world.has_entity(target_id):
            continue
        body = world.get_entity(target_id)
        if body.has_component(CelestialBodyComponent):
            names.append(body.get_component(CelestialBodyComponent).name)
    if not names:
        return []
    charted = ", ".join(sorted(names))
    return [f"You are tracking {len(names)} wanderers: {charted}."]


TRACK_BODY_DEF = ActionDefinition(
    command_type="track-body",
    title="Track a body",
    description="Chart a planet or comet that is up tonight and within your telescope's reach.",
    lane=Lane.WORLD,
    cost=CommandCost(action=1),
    arguments={
        "body": ActionArgument(
            title="Body",
            description="Name a planet or comet above the horizon tonight to chart it.",
            kind="string",
        ),
    },
)

TRACK_ACTION_DEFINITIONS = (TRACK_BODY_DEF,)
TRACK_ACTION_HANDLERS = (TrackBodyHandler,)


__all__ = [
    "FIRST_SIGHTING_MOOD",
    "TELESCOPE_BONUS",
    "TRACK_ACTION_DEFINITIONS",
    "TRACK_ACTION_HANDLERS",
    "TRACK_BODY_DEF",
    "TRACK_MOOD",
    "TrackBodyHandler",
    "TracksBody",
    "record_tracking",
    "tracking_fragments",
]
