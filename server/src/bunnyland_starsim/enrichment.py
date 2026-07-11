"""Declarative telescope generation enrichment."""

from bunnyland.core import (
    ContainmentMode,
    Contains,
    HoldableComponent,
    IdentityComponent,
    PortableComponent,
)
from bunnyland.core.generation import GenerationChild, GenerationDelta, GenerationRequest

from .components import TelescopeComponent
from .telescopes import TELESCOPE_TIERS

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


class StarsimGenerationEnricher:
    capabilities: tuple[str, ...] = ()

    def applies(self, request: GenerationRequest) -> bool:
        return request.entity_kind == "room"

    def enrich(self, request: GenerationRequest) -> GenerationDelta:
        room = next(
            (
                item
                for item in request.context.get("base_components", ())
                if item.__class__.__name__ == "RoomComponent"
            ),
            None,
        )
        text = " ".join(
            (
                request.source_key,
                request.description,
                str(getattr(room, "biome", "")),
                *request.tags,
            )
        ).casefold()
        if not any(term in text for term in OBSERVATORY_TERMS):
            return GenerationDelta()
        power = next(tier.min_power for tier in TELESCOPE_TIERS if tier.name == "field telescope")
        return GenerationDelta(
            children=(
                GenerationChild(
                    request=GenerationRequest(
                        entity_kind="item",
                        description="telescope",
                        source_seed=request.source_seed,
                        source_key=f"{request.source_key}:telescope",
                        tags=("starsim",),
                    ),
                    parent_edge=Contains(mode=ContainmentMode.ROOM_CONTENT),
                    components=(
                        IdentityComponent(name="telescope", kind="item", tags=("starsim",)),
                        PortableComponent(),
                        HoldableComponent(slot="hand"),
                        TelescopeComponent(power=power),
                    ),
                ),
            )
        )


__all__ = ["OBSERVATORY_TERMS", "StarsimGenerationEnricher"]
