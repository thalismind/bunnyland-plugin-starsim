# bunnyland-starsim (server plugin)

The out-of-tree Bunnyland plugin package `bunnyland_starsim` (plugin id `bunnyland.starsim`).

## Development

Tests run against a sibling `bunnyland-server` checkout without installing anything —
`tests/conftest.py` puts both this package's `src/` and `../bunnyland-server/src` on
`sys.path`. From this `server/` directory:

```bash
# uses the sibling bunnyland-server's virtualenv/deps
uv run --project ../../bunnyland-server -m pytest
# or, if bunnyland + relics are already importable:
python -m pytest
```

Lint:

```bash
uv run ruff check src tests
```

## Loading into the server

```bash
bunnyland serve --module bunnyland_starsim
```

`default_enabled=True`, so no `--plugin` flag is required once the module is imported.

## What it contributes

- **Components** — `SkyComponent` (a singleton on the world clock), `TelescopeComponent` (a
  held item), `ConstellationLogComponent` and `WishLogComponent` (on characters).
- **The turning sky** — `NightSkyConsequence` derives the sky from the clock's time of day,
  season, and weather every tick and stores it as the `SkyComponent` singleton. Stars are out
  only at night, under clear skies; per-character visibility additionally requires an outdoor
  room. It emits a `SkyChangedEvent` when the celestial event overhead begins or ends. Fully
  deterministic — the calendar drives everything.
- **Constellations** — a fixed catalogue (`constellations.CATALOGUE`) of circumpolar and
  seasonal figures. `constellations_up(season)` gives tonight's sorted set; `stargaze` charts
  a named one into the character's `ConstellationLogComponent`.
- **Celestial events** — `celestial_event_for(day)` returns a deterministic meteor shower or
  comet for a calendar day. `make-a-wish` succeeds only when a wishing event is visible (a
  clear night, outdoors), tallies the wish, and lifts the wisher's mood.
- **Navigation by stars** — `navigation_fragments` surfaces the pole star as due north when
  the stars are visible.
- **Prompt fragments** — `sky_fragments` (tonight's sky), `navigation_fragments` (cardinal
  cue), and `constellation_fragments` (first-person log).
- **Two verbs** — `stargaze` and `make-a-wish` — usable by the character (human or AI).
- **Spawn factory** — `spawn_telescope`.

## Reuses

`WorldClockComponent` and the environment mechanic's `time_of_day` / `weather_for` /
`WeatherComponent` (clouds hide stars), `RoomComponent.indoor`, and the core affect system
(`AffectDelta` / thoughts) for the calm and wonder of a clear night.
