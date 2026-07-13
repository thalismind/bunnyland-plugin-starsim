# Bunnyland Starsim

Out-of-tree [Bunnyland](https://github.com/thalismind/bunnyland-server) plugin that adds a
**stargazing and astronomy** pack — a quiet, contemplative expansion-pack-sized bundle of a
few mechanics that reuse the clock and weather Bunnyland already ships. Look up: the sky keeps
time and secrets.

The night sky **turns with the calendar** — stars are only out at night, under clear skies,
in outdoor rooms — so weather and time of day suddenly matter, gently. Everything is fully
deterministic: the calendar drives the whole sky, with no randomness or wall-clock reads.

## Mechanics

- **The turning sky** — a `NightSkyConsequence` derives the visible sky (`SkyComponent`, a
  singleton on the world clock) from the clock, season, and weather every tick. Stars are out
  only at night, under clear skies; clouds hide them.
- **Stargaze** — the `stargaze` verb reports the sky and lifts the gazer's mood (calm and
  wonder), deepened by a held `TelescopeComponent`.
- **Constellations** — a fixed catalogue of circumpolar and seasonal figures; the
  `ConstellationLogComponent` records which a character has charted, rewarding return visits.
- **Celestial events** — deterministic meteor showers and comets on the calendar, with a
  `make-a-wish` verb that grants a small, flavourful boon when a wishing event is overhead.
- **Navigation by stars** — outdoors under a clear night sky, the pole star fixes due north,
  complementing a mapping/cartography pack.

This repo intentionally keeps all starsim work outside the main `bunnyland-server` repo.

## Layout

- `server/` - Python Bunnyland plugin package with the sky/constellation/telescope components,
  the night-sky consequence, prompt fragments, the two player/AI verbs, a spawn factory, and
  tests.

## Server Plugin

The plugin exposes `bunnyland_starsim.bunnyland_plugins()` and contributes:

- `SkyComponent`, `TelescopeComponent`, `ConstellationLogComponent`, `WishLogComponent`.
- `NightSkyConsequence` - derives the singleton sky from the clock each tick and emits a
  `SkyChangedEvent` when a celestial event begins or ends.
- `sky_fragments`, `navigation_fragments`, `constellation_fragments` - prompt fragments for
  both human and AI prompts.
- `stargaze` and `make-a-wish` - verbs for the character (human or AI), emitting
  `StargazedEvent`, `ConstellationIdentifiedEvent`, and `WishMadeEvent`.
- `spawn_telescope` - a spawn factory for the optional telescope item.
- Optional Bunnyland 3D integration models telescopes and projects a starfield skybox only
  in outdoor rooms where the calendar and weather make the stars visible.

No worldgen hook is required: the sky is global.

## Running

This package builds no containers. It is loaded into the stock server via `--module`:

```bash
bunnyland serve --module bunnyland_starsim
```

`default_enabled=True`, so no `--plugin` flag is required once the module is imported. The
`bunnyland_starsim` package must be importable by the server (installed into the server's
environment, or on `PYTHONPATH`).

## Development

Run server tests against a sibling `bunnyland-server` checkout (no install required —
`server/tests/conftest.py` puts both packages on `sys.path`). From `server/`:

```bash
uv run --project ../../bunnyland-server -m pytest
uv run --project ../../bunnyland-server ruff check src tests
```

See [`server/README.md`](server/README.md) for more detail.

## Contributing & Conduct

This plugin follows the Bunnyland project's
[contribution guidelines](CONTRIBUTING.md) and [code of conduct](CODE_OF_CONDUCT.md),
which point back to the `bunnyland-server` repository.

## License

Licensed under the GNU Affero General Public License v3.0. See [LICENSE](LICENSE).
