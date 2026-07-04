"""Celestial events and the ``make-a-wish`` verb.

Meteor showers and comets are **entirely calendar-driven** — no randomness, no wall-clock —
so a given day always has the same event overhead. A meteor shower peaks on a fixed period
of days; a comet returns on one day of the year.

The ``make-a-wish`` verb only succeeds when a wishing event is overhead *and* the stars are
actually visible to the character (a clear night, outdoors). It grants a small, flavourful
boon by lifting the wisher's mood (wonder and confidence) and tallies the wish. This is the
natural tie-in point for a luck mechanic such as Fortunesim, if one is loaded, but starsim
keeps no hard dependency on it.
"""

from __future__ import annotations

from dataclasses import replace

from bunnyland.core.actions import ActionDefinition
from bunnyland.core.commands import CommandCost, Lane, SubmittedCommand
from bunnyland.core.components import AffectDelta
from bunnyland.core.ecs import replace_component
from bunnyland.core.events import EventVisibility
from bunnyland.core.handlers import HandlerContext, HandlerResult, ok, rejected, require_character
from bunnyland.mechanics.environment import DAYS_PER_SEASON, SEASONS

from .affect import lift_mood
from .components import WishLogComponent
from .events import WishMadeEvent
from .spatial import room_of

#: Length of a full in-world year in days (four 28-day seasons).
DAYS_PER_YEAR = DAYS_PER_SEASON * len(SEASONS)

#: Event names.
METEOR_SHOWER = "meteor shower"
COMET = "comet"

#: A meteor shower peaks every this-many days.
METEOR_SHOWER_PERIOD = 14
#: A comet returns on this day of the year (takes precedence over a shower on the same day).
COMET_DAY_OF_YEAR = 42

#: Events you may wish upon.
WISH_EVENTS: tuple[str, ...] = (COMET, METEOR_SHOWER)

#: The mood lift a granted wish confers (wonder + confidence).
WISH_MOOD = AffectDelta(valence=8.0, stress=-4.0, confidence=6.0, curiosity=4.0)


def celestial_event_for(day: int) -> str:
    """Return the celestial event overhead on ``day`` (``""`` when the sky is quiet)."""
    if day < 1:
        return ""
    day_of_year = (day - 1) % DAYS_PER_YEAR + 1
    if day_of_year == COMET_DAY_OF_YEAR:
        return COMET
    if day % METEOR_SHOWER_PERIOD == 0:
        return METEOR_SHOWER
    return ""


class MakeAWishHandler:
    """Wish upon a celestial event visible from an outdoor room on a clear night."""

    command_type = "make-a-wish"

    def execute(self, ctx: HandlerContext, command: SubmittedCommand) -> HandlerResult:
        # Imported lazily to avoid a module import cycle: sky imports this module's
        # ``celestial_event_for`` at load time.
        from .sky import derive_sky, stars_visible_from_room

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
        if sky.event not in WISH_EVENTS:
            return rejected("there is nothing to wish upon right now")

        log = (
            character.get_component(WishLogComponent)
            if character.has_component(WishLogComponent)
            else WishLogComponent()
        )
        updated = replace(log, wishes=log.wishes + 1, last_event=sky.event)
        if character.has_component(WishLogComponent):
            replace_component(character, updated)
        else:
            character.add_component(updated)
        lift_mood(ctx.world, character, WISH_MOOD, ctx.epoch)
        return ok(
            WishMadeEvent(
                **ctx.event_base(
                    visibility=EventVisibility.ROOM,
                    actor_id=str(character_id),
                    room_id=str(room.id),
                    celestial_event=sky.event,
                )
            )
        )


def _no_stars_reason(sky, room) -> str:
    """A specific rejection reason for why the stars cannot be seen right now."""
    from bunnyland.core import RoomComponent

    if room.has_component(RoomComponent) and room.get_component(RoomComponent).indoor:
        return "you are indoors; you cannot see the sky"
    if sky.phase != "night":
        return "the stars are not out"
    return "clouds hide the stars"


MAKE_A_WISH_DEF = ActionDefinition(
    command_type="make-a-wish",
    title="Make a wish",
    description="Wish upon a meteor shower or comet visible from an open, clear night sky.",
    lane=Lane.WORLD,
    cost=CommandCost(action=1),
    arguments={},
)

CELESTIAL_ACTION_DEFINITIONS = (MAKE_A_WISH_DEF,)
CELESTIAL_ACTION_HANDLERS = (MakeAWishHandler,)


__all__ = [
    "CELESTIAL_ACTION_DEFINITIONS",
    "CELESTIAL_ACTION_HANDLERS",
    "COMET",
    "COMET_DAY_OF_YEAR",
    "DAYS_PER_YEAR",
    "MAKE_A_WISH_DEF",
    "METEOR_SHOWER",
    "METEOR_SHOWER_PERIOD",
    "WISH_EVENTS",
    "WISH_MOOD",
    "MakeAWishHandler",
    "celestial_event_for",
]
