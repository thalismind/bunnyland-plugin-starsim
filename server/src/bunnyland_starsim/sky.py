"""The turning sky: derive tonight's visible sky from the world clock.

:func:`derive_sky` reads the singleton world clock and produces a :class:`SkyComponent` that
captures the phase, season, weather, which constellations are up, and any celestial event —
all *purely* from the calendar, so the sky is fully deterministic and reproducible. Stars are
out only at **night** under a **clear** sky; whether a given character can actually see them
additionally requires an **outdoor** room, checked by :func:`stars_visible_from_room`.

:class:`NightSkyConsequence` stores the derived sky on the clock each tick (a singleton, like
the core time-of-day and weather components) and emits a :class:`SkyChangedEvent` when the
celestial event overhead begins or ends.
"""

from __future__ import annotations

from bunnyland.core import RoomComponent, WorldClockComponent
from bunnyland.core.ecs import replace_component
from bunnyland.core.events import DomainEvent, EventVisibility, event_base
from bunnyland.mechanics.environment import (
    WeatherComponent,
    time_of_day,
    weather_for,
)
from relics import Entity, World

from .celestial import celestial_event_for
from .components import SkyComponent
from .constellations import constellations_up
from .events import SkyChangedEvent
from .spatial import room_of

#: Weather conditions under which the stars are visible. Anything cloudier hides them.
CLEAR_CONDITIONS: tuple[str, ...] = ("clear",)

#: The phase during which stars are out.
NIGHT = "night"


def _clock_entity(world: World) -> Entity | None:
    clocks = list(world.query().with_all([WorldClockComponent]).execute_entities())
    return clocks[0] if clocks else None


def derive_sky(world: World) -> SkyComponent | None:
    """Compute the current :class:`SkyComponent` from the world clock, or ``None``.

    Weather is taken from an explicit :class:`WeatherComponent` on the clock when present
    (so the environment mechanic or a test can drive it), else derived from the calendar.
    """
    clock = _clock_entity(world)
    if clock is None:
        return None
    seconds = clock.get_component(WorldClockComponent).game_time_seconds
    day, _hour, phase, season = time_of_day(seconds)
    if clock.has_component(WeatherComponent):
        condition = clock.get_component(WeatherComponent).condition
    else:
        condition, _intensity = weather_for(day)
    stars_out = phase == NIGHT and condition in CLEAR_CONDITIONS
    return SkyComponent(
        day=day,
        season=season,
        phase=phase,
        condition=condition,
        stars_out=stars_out,
        constellations=constellations_up(season),
        event=celestial_event_for(day),
    )


def stars_visible_from_room(sky: SkyComponent, room: Entity | None) -> bool:
    """Whether the stars in ``sky`` can be seen from ``room`` (outdoors, clear night)."""
    if sky is None or not sky.stars_out or room is None:
        return False
    if not room.has_component(RoomComponent):
        return False
    return not room.get_component(RoomComponent).indoor


class NightSkyConsequence:
    """Store the derived sky on the clock each tick and announce event changes."""

    def process(self, world: World, epoch: int) -> list[DomainEvent]:
        clock = _clock_entity(world)
        if clock is None:
            return []
        sky = derive_sky(world)
        previous = clock.get_component(SkyComponent) if clock.has_component(SkyComponent) else None
        replace_component(clock, sky)
        if previous is not None and previous.event != sky.event:
            return [
                SkyChangedEvent(
                    **event_base(
                        epoch,
                        default_visibility=EventVisibility.PUBLIC,
                        celestial_event=sky.event,
                        phase=sky.phase,
                    )
                )
            ]
        return []


def sky_fragments(world: World, character: Entity) -> list[str]:
    """Describe tonight's visible sky for a character standing under open, clear night."""
    if character is None:
        return []
    sky = derive_sky(world)
    room = room_of(world, character.id)
    if not stars_visible_from_room(sky, room):
        return []
    lines = [f"The night sky is clear over {sky.season}; the stars are out."]
    if sky.constellations:
        lines.append(f"Overhead you can pick out {', '.join(sky.constellations)}.")
    if sky.event:
        lines.append(f"A {sky.event} is crossing the sky tonight.")
    return sorted(dict.fromkeys(lines))


__all__ = [
    "CLEAR_CONDITIONS",
    "NIGHT",
    "NightSkyConsequence",
    "derive_sky",
    "sky_fragments",
    "stars_visible_from_room",
]
