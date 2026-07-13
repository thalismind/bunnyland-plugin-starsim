"""The ``stargaze`` verb: look up, take in the sky, and chart a constellation.

Stargazing only works where the stars are actually visible — an outdoor room, at night,
under a clear sky — so its rejections mirror those conditions. A successful gaze lifts the
gazer's mood (calm and wonder), deepened if they are holding a :class:`TelescopeComponent`.
Passing an optional ``constellation`` charts it into the character's
:class:`~bunnyland_starsim.components.ConstellationLogComponent` when it is up tonight,
rewarding return visits across the seasons with a little extra wonder.

Validation order follows the project convention: invalid id -> missing entity -> not in a
room -> cannot see the sky -> invalid argument -> apply.
"""

from __future__ import annotations

from bunnyland.core import RoomComponent, contents
from bunnyland.core.actions import ActionArgument, ActionDefinition, ActionEffort, effort_cost
from bunnyland.core.commands import Lane, SubmittedCommand
from bunnyland.core.components import AffectDelta
from bunnyland.core.events import EventVisibility
from bunnyland.core.handlers import (
    HandlerContext,
    HandlerResult,
    planned,
    rejected,
    require_character,
)
from bunnyland.core.mutations import MutationPlan, SetComponent
from relics import Entity, World

from .affect import mood_operations
from .components import ConstellationLogComponent, TelescopeComponent
from .constellations import is_known_constellation
from .events import ConstellationIdentifiedEvent, StargazedEvent
from .sky import derive_sky, stars_visible_from_room
from .spatial import room_of

#: Base mood lift from a plain, naked-eye gaze (calm + a little wonder).
GAZE_MOOD = AffectDelta(valence=4.0, stress=-3.0, curiosity=2.0)
#: Extra wonder when charting a new constellation.
DISCOVERY_MOOD = AffectDelta(valence=3.0, curiosity=3.0)
#: Multiplier applied to every mood dimension while a telescope is in hand.
TELESCOPE_BONUS = 1.5


def _held_telescope(world: World, character: Entity) -> TelescopeComponent | None:
    """Return the strongest telescope the character is carrying, or ``None``."""
    best: TelescopeComponent | None = None
    for item_id in contents(character):
        if not world.has_entity(item_id):
            continue
        item = world.get_entity(item_id)
        if item.has_component(TelescopeComponent):
            telescope = item.get_component(TelescopeComponent)
            if best is None or telescope.power > best.power:
                best = telescope
    return best


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


class StargazeHandler:
    """Look up at a clear night sky, lift the gazer's mood, and chart a constellation."""

    command_type = "stargaze"

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

        requested = (command.payload.get("constellation") or "").strip()
        identified_new = False
        if requested:
            if not is_known_constellation(requested):
                return rejected("that is not a constellation you know of")
            if requested not in sky.constellations:
                return rejected("that constellation is not visible tonight")
            log = (
                character.get_component(ConstellationLogComponent)
                if character.has_component(ConstellationLogComponent)
                else ConstellationLogComponent()
            )
            identified_new = requested not in log.identified

        telescope = _held_telescope(ctx.world, character)
        mood = GAZE_MOOD
        if identified_new:
            mood = _sum(mood, DISCOVERY_MOOD)
        if telescope is not None:
            mood = _scaled(mood, TELESCOPE_BONUS * telescope.power)
        operations = []
        if identified_new:
            operations.append(
                SetComponent(
                    character.id,
                    ConstellationLogComponent(
                        identified=tuple(sorted({*log.identified, requested}))
                    ),
                )
            )
        operations.extend(mood_operations(character, mood, ctx.epoch))

        events = [
            StargazedEvent(
                **ctx.event_base(
                    visibility=EventVisibility.ROOM,
                    actor_id=str(character_id),
                    room_id=str(room.id),
                    phase=sky.phase,
                    constellation=requested,
                )
            )
        ]
        if identified_new:
            events.append(
                ConstellationIdentifiedEvent(
                    **ctx.event_base(
                        visibility=EventVisibility.ROOM,
                        actor_id=str(character_id),
                        room_id=str(room.id),
                        constellation=requested,
                    )
                )
            )
        return planned(MutationPlan(tuple(operations)), *events)


STARGAZE_DEF = ActionDefinition(
    command_type="stargaze",
    title="Stargaze",
    description="Look up at a clear night sky and, optionally, chart a constellation.",
    lane=Lane.FOCUS,
    cost=effort_cost(focus=ActionEffort.ROUTINE),
    arguments={
        "constellation": ActionArgument(
            title="Constellation",
            description="Name a constellation up tonight to chart it; omit to simply gaze.",
            kind="string",
        ),
    },
)

STARGAZE_ACTION_DEFINITIONS = (STARGAZE_DEF,)
STARGAZE_ACTION_HANDLERS = (StargazeHandler,)


__all__ = [
    "DISCOVERY_MOOD",
    "GAZE_MOOD",
    "STARGAZE_ACTION_DEFINITIONS",
    "STARGAZE_ACTION_HANDLERS",
    "STARGAZE_DEF",
    "TELESCOPE_BONUS",
    "StargazeHandler",
]
