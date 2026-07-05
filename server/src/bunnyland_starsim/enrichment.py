"""World-generation enrichment: put a telescope where the sky is worth watching.

When the generator emits a room that reads like a vantage for the sky — an observatory, a
tower, a hilltop, a rooftop — this hook drops a telescope into it, so generated worlds already
give a stargazer somewhere to track the planets and comets from. Detection is text-based and
deterministic; nothing here is random, and the core generator never learns this plugin exists.
"""

from __future__ import annotations

from bunnyland.core import contents
from bunnyland.core.ecs import parse_entity_id
from bunnyland.core.events import RoomGeneratedEvent
from bunnyland.core.world_actor import WorldActor

from .components import TelescopeComponent
from .prefabs import spawn_tiered_telescope

#: Room text that marks a generated room as a stargazing vantage.
OBSERVATORY_TERMS = (
    "observatory",
    "planetarium",
    "tower",
    "rooftop",
    "roof",
    "hilltop",
    "hill",
    "summit",
    "belvedere",
    "lookout",
    "watchtower",
)


class StarsimWorldgenHook:
    """Seed a telescope into generated observatories and other stargazing vantages."""

    def subscribe(self, actor: WorldActor) -> None:
        self._actor = actor
        actor.bus.subscribe(RoomGeneratedEvent, self._on_room)

    def _on_room(self, event: RoomGeneratedEvent) -> None:
        entity_id = parse_entity_id(event.entity_id)
        if entity_id is None or not self._actor.world.has_entity(entity_id):
            return
        if not _is_vantage(event):
            return
        world = self._actor.world
        room = world.get_entity(entity_id)
        # Idempotent: never seed a telescope into the same room twice.
        for existing_id in contents(room):
            if world.has_entity(existing_id) and world.get_entity(existing_id).has_component(
                TelescopeComponent
            ):
                return
        spawn_tiered_telescope(world, "field telescope", room_id=room.id)


def _is_vantage(event: RoomGeneratedEvent) -> bool:
    text = " ".join(
        (
            event.room_key,
            event.biome,
            event.generation.description,
            *event.generation.tags,
        )
    ).casefold()
    return any(term in text for term in OBSERVATORY_TERMS)


__all__ = ["OBSERVATORY_TERMS", "StarsimWorldgenHook"]
