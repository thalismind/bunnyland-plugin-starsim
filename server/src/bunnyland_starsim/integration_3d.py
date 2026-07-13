"""Optional, lazily imported 3D appearance for telescopes."""

from .components import TelescopeComponent
from .sky import derive_sky, stars_visible_from_room


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
        RoomSkyboxRule,
        Skybox3D,
        VisualMaterial3D,
        register_entity_visuals,
        register_models,
        register_skybox_rules,
        register_skyboxes,
    )

    owner = "bunnyland.starsim"
    model_key = f"{owner}/telescope"
    register_skyboxes(
        actor,
        owner,
        (
            Skybox3D(
                f"{owner}/clear-night",
                zenith_color="#030817",
                sky_color="#09152f",
                horizon_color="#172544",
                horizon_mix=0.78,
                sun_color="#dbe8ff",
                sun_x=0.72,
                sun_y=0.22,
                sun_size=0.018,
                sun_opacity=0.82,
                cloud_color="#9eb2cc",
                cloud_opacity=0.05,
                cloud_count=4,
                star_color="#edf4ff",
                star_opacity=0.9,
                star_count=220,
            ),
        ),
    )
    register_skybox_rules(
        actor,
        owner,
        (
            RoomSkyboxRule(
                f"{owner}/visible-night-sky",
                f"{owner}/clear-night",
                lambda world, room: stars_visible_from_room(derive_sky(world), room),
                priority=20,
            ),
        ),
    )
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
