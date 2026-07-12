"""Optional, lazily imported 3D appearance for telescopes."""

from .components import TelescopeComponent


def install_starsim_3d(actor, context) -> None:
    if context.plugins is None or not context.plugins.enabled("bunnyland.3d"):
        return
    from bunnyland_3d import (
        EntityVisualContribution,
        EntityVisualRule,
        ModelAsset,
        ModelTransform,
        PrimitivePart3D,
        ProceduralModelSource,
        VisualMaterial3D,
        register_entity_visuals,
        register_models,
    )

    owner = "bunnyland.starsim"
    model_key = f"{owner}/telescope"
    metal = VisualMaterial3D(color="#71839b", metallic=0.7, roughness=0.3)
    register_models(
        actor,
        owner,
        (
            ModelAsset(
                key=model_key,
                source=ProceduralModelSource(
                    parts=(
                        PrimitivePart3D(
                            "tube",
                            "cylinder",
                            radius=0.16,
                            height=1.1,
                            transform=ModelTransform(rotation=(0, 0, 1.2), translation=(0, 1.2, 0)),
                            material=metal,
                            roles=("damageable", "state-indicator"),
                        ),
                        PrimitivePart3D(
                            "tripod_hub",
                            "sphere",
                            radius=0.13,
                            transform=ModelTransform(translation=(0, 0.78, 0)),
                            material=metal,
                        ),
                        PrimitivePart3D(
                            "tripod_left",
                            "cylinder",
                            radius=0.035,
                            height=0.9,
                            transform=ModelTransform(
                                rotation=(0, 0, -0.32), translation=(-0.14, 0.38, 0)
                            ),
                            material=metal,
                        ),
                        PrimitivePart3D(
                            "tripod_right",
                            "cylinder",
                            radius=0.035,
                            height=0.9,
                            transform=ModelTransform(
                                rotation=(0, 0, 0.32), translation=(0.14, 0.38, 0)
                            ),
                            material=metal,
                        ),
                        PrimitivePart3D(
                            "tripod_back",
                            "cylinder",
                            radius=0.035,
                            height=0.9,
                            transform=ModelTransform(
                                rotation=(0.32, 0, 0), translation=(0, 0.38, 0.14)
                            ),
                            material=metal,
                        ),
                    )
                ),
            ),
        ),
    )
    register_entity_visuals(
        actor,
        owner,
        (
            EntityVisualRule(
                key=f"{owner}/telescope",
                predicate=lambda entity: entity.has_component(TelescopeComponent),
                contribution=EntityVisualContribution(base_model_key=model_key),
            ),
        ),
    )


__all__ = ["install_starsim_3d"]
