"""Mood helper: lift a character's affect by spawning a decaying thought.

Bunnyland models mood through short-lived *thought* entities carrying an ``AffectDelta``;
the core ``AffectAggregation`` consequence sums the active thoughts into a character's current
mood each tick. A quiet, contemplative pack like starsim nudges mood the same way the core
reactor does — by attaching a thought — rather than writing the aggregate directly, so it
composes cleanly with every other affect source.
"""

from __future__ import annotations

from bunnyland.core import (
    AffectDelta,
    CharacterComponent,
    HasThought,
    ThoughtComponent,
    spawn_entity,
)
from bunnyland.core.mutations import AddEdge, AddEntity, EntityReference
from relics import Entity, World

#: How long a stargazing thought lingers before it decays (game seconds).
WONDER_TTL_SECONDS = 2 * 3600


def lift_mood(
    world: World,
    character: Entity,
    delta: AffectDelta,
    epoch: int,
    *,
    label: str = "wonder",
    text: str = "The night sky is quietly beautiful.",
) -> Entity | None:
    """Attach a decaying thought carrying ``delta`` to ``character``.

    Returns the spawned thought entity, or ``None`` if the target is not a character.
    """
    if character is None or not character.has_component(CharacterComponent):
        return None
    thought = spawn_entity(
        world,
        [
            ThoughtComponent(
                label=label,
                text=text,
                affect_delta=delta,
                created_at_epoch=epoch,
                expires_at_epoch=epoch + WONDER_TTL_SECONDS,
            )
        ],
    )
    character.add_relationship(HasThought(), thought.id)
    return thought


def mood_operations(
    character: Entity,
    delta: AffectDelta,
    epoch: int,
    *,
    label: str = "wonder",
    text: str = "The night sky is quietly beautiful.",
):
    """Build typed operations for a decaying mood thought without mutating the world."""
    if character is None or not character.has_component(CharacterComponent):
        return ()
    thought = EntityReference()
    return (
        AddEntity(
            (
                ThoughtComponent(
                    label=label,
                    text=text,
                    affect_delta=delta,
                    created_at_epoch=epoch,
                    expires_at_epoch=epoch + WONDER_TTL_SECONDS,
                ),
            ),
            reference=thought,
        ),
        AddEdge(character.id, thought, HasThought()),
    )


__all__ = ["WONDER_TTL_SECONDS", "lift_mood", "mood_operations"]
