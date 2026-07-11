from __future__ import annotations

from bunnyland.core import (
    WorldActor,
    WorldClockComponent,
    replace_component,
    spawn_entity,
)
from bunnyland.foundation.storyteller.mechanics import (
    IncidentComponent,
    IncidentResolvedEvent,
    IncidentStartedEvent,
)
from relics import World

from bunnyland_starsim.events import CelestialEventBeganEvent
from bunnyland_starsim.incident import CelestialIncidentConsequence

SECONDS_PER_HOUR = 3600
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR
NIGHT = 2 * SECONDS_PER_HOUR
COMET_NIGHT = 41 * SECONDS_PER_DAY + NIGHT  # day 42
METEOR_NIGHT = 13 * SECONDS_PER_DAY + NIGHT  # day 14


def _clock(actor):
    return list(actor.world.query().with_all([WorldClockComponent]).execute_entities())[0]


def _set_time(actor, seconds):
    replace_component(_clock(actor), WorldClockComponent(game_time_seconds=seconds))


def _incidents(actor):
    return list(actor.world.query().with_all([IncidentComponent]).execute_entities())


def test_no_clock_produces_nothing():
    assert CelestialIncidentConsequence().process(World(), 0) == []


def test_quiet_sky_opens_no_incident():
    actor = WorldActor()  # day 1, quiet
    assert CelestialIncidentConsequence().process(actor.world, 0) == []
    assert _incidents(actor) == []


def test_a_comet_opens_a_storyteller_incident_and_publishes_a_spectacle():
    actor = WorldActor()
    _set_time(actor, COMET_NIGHT)
    events = CelestialIncidentConsequence().process(actor.world, 5)

    assert any(isinstance(e, IncidentStartedEvent) and e.kind == "comet" for e in events)
    began = next(e for e in events if isinstance(e, CelestialEventBeganEvent))
    assert began.spectacle == "comet"
    assert began.celestial_event == "comet"
    # A real core incident entity now exists, keyed to the comet.
    incidents = _incidents(actor)
    assert len(incidents) == 1
    incident = incidents[0].get_component(IncidentComponent)
    assert incident.kind == "comet"
    assert incident.resolved_at_epoch is None


def test_a_foreign_incident_is_ignored_when_scanning():
    actor = WorldActor()
    # Another pack's incident (a different kind) must not be mistaken for the celestial one.
    spawn_entity(
        actor.world,
        [IncidentComponent(kind="hostile_encounter", budget_spent=0.0, started_at_epoch=0)],
    )
    _set_time(actor, COMET_NIGHT)
    events = CelestialIncidentConsequence().process(actor.world, 5)
    assert any(isinstance(e, IncidentStartedEvent) and e.kind == "comet" for e in events)
    open_celestial = [
        i for i in _incidents(actor) if i.get_component(IncidentComponent).kind == "comet"
    ]
    assert len(open_celestial) == 1


def test_a_meteor_shower_opens_its_own_incident_kind():
    actor = WorldActor()
    _set_time(actor, METEOR_NIGHT)
    events = CelestialIncidentConsequence().process(actor.world, 1)
    assert any(isinstance(e, IncidentStartedEvent) and e.kind == "meteor_shower" for e in events)


def test_an_open_incident_is_not_reopened_while_it_persists():
    actor = WorldActor()
    _set_time(actor, COMET_NIGHT)
    consequence = CelestialIncidentConsequence()
    consequence.process(actor.world, 5)
    assert consequence.process(actor.world, 6) == []  # unchanged sky -> no churn
    assert len(_incidents(actor)) == 1


def test_incident_resolves_when_the_sky_goes_quiet():
    actor = WorldActor()
    consequence = CelestialIncidentConsequence()
    _set_time(actor, COMET_NIGHT)
    consequence.process(actor.world, 5)

    _set_time(actor, NIGHT)  # back to a quiet day-1 sky
    events = consequence.process(actor.world, 9)
    assert any(isinstance(e, IncidentResolvedEvent) and e.kind == "comet" for e in events)
    incident = _incidents(actor)[0].get_component(IncidentComponent)
    assert incident.resolved_at_epoch == 9


def test_a_new_event_resolves_the_old_incident_and_opens_a_fresh_one():
    actor = WorldActor()
    consequence = CelestialIncidentConsequence()
    _set_time(actor, COMET_NIGHT)
    consequence.process(actor.world, 5)

    _set_time(actor, METEOR_NIGHT)
    events = consequence.process(actor.world, 20)
    assert any(isinstance(e, IncidentResolvedEvent) and e.kind == "comet" for e in events)
    assert any(isinstance(e, IncidentStartedEvent) and e.kind == "meteor_shower" for e in events)
    open_kinds = {
        i.get_component(IncidentComponent).kind
        for i in _incidents(actor)
        if i.get_component(IncidentComponent).resolved_at_epoch is None
    }
    assert open_kinds == {"meteor_shower"}
