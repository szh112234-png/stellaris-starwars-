# AGENTS.md — FOC AI/Codex Working Contract

This repository is a live Stellaris mod project. AI agents must treat gameplay behavior, event chains, compatibility, model assets, and existing player-facing features as production code.

## Before editing

1. Read `docs/PROJECT_RULES.md`.
2. Read `docs/TEST_PLAN.md` and identify the regression cases touched by the task.
3. Inspect the relevant current files before proposing changes; do not reconstruct behavior from memory alone.
4. Keep `main` stable. Work on a branch and use a PR for non-trivial changes.

## Editing rules

- Make the smallest coherent change that satisfies the task.
- Do not perform unrelated cleanup or mass formatting.
- Do not silently remove existing functionality.
- Preserve FOC standalone operation and the SG compatibility boundary defined in `docs/PROJECT_RULES.md`.
- Scripted-effect call depth must remain <= 5.
- Ordinary Stellaris text: UTF-8 without BOM. Localisation `.yml`: UTF-8 with BOM.
- Do not change binary assets unless the task explicitly requires an asset/model/audio change.
- When editing ship/model definitions, preserve locator, section, slot and entity/asset references unless intentionally changed.

## Verification

Run:

```bash
python tools/preflight.py
```

For repository-wide baseline auditing without blocking on inherited legacy findings, use:

```bash
python tools/preflight.py --report-only
```

Then perform the relevant manual checks in `docs/TEST_PLAN.md`.

## Required completion report

Every implementation report should include:

- root cause or intended design change;
- files changed;
- important behavioral differences;
- automated checks run and their result;
- manual/in-game checks still required;
- known risks or compatibility implications.

Do not claim a gameplay fix is fully verified if it has not been tested in Stellaris.
