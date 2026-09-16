# Star Wars Fall of the Republic — Project Rules

This file defines the repository's durable engineering rules. Gameplay design can evolve, but any intentional change to an invariant below should update this document and the regression test plan in the same PR.

## 1. Source of truth and change control

- `main` is the stable source of truth. Release ZIPs are build artifacts, not development baselines.
- Work on feature/fix/chore branches and merge through pull requests.
- Do not remove, rewrite, or silently disable existing features unless the task explicitly requires it.
- Avoid unrelated cleanup, mass reformatting, filename churn, or line-ending-only changes in functional PRs.
- Keep changes as narrow as practical and document risky cross-system effects.

## 2. Encoding and line endings

- Normal Stellaris `.txt`/`.mod`/`.gui`/`.gfx`/`.asset` text files: UTF-8 without BOM.
- Stellaris localisation `.yml` files under `localisation/`: UTF-8 with BOM.
- Repository text files use LF line endings; `.gitattributes` controls checkout normalization.
- Do not add a blanket UTF-8 BOM to ordinary text files.

## 3. Script safety

- Scripted-effect call depth must never exceed 5.
- Avoid recursive or mutually recursive scripted-effect chains. Prefer explicit staged effects when a chain approaches the limit.
- Event IDs, localisation keys, scripted effects, technologies, components, ship sizes, sections, assets, entities and resources should use stable, collision-resistant FOC-prefixed identifiers where feasible.
- Never declare a task complete while known parser errors, missing references, duplicate event IDs, or broken localisation introduced by that task remain.

## 4. Compatibility boundary

- FOC must remain usable without SG enabled.
- When FOC and SG are enabled together, shared-resource compatibility must not be implemented by overwriting SG components, technologies, events, buildings, or economy rules.
- Current compatibility policy: only the explicitly shared resource inventory/IDs are shared (currently Kyber crystal and Tibanna gas). FOC-owned Coaxium/Beskar definitions remain FOC-controlled unless the design is intentionally changed.
- Never make SG a hard dependency for ordinary FOC gameplay logic.

## 5. High-risk gameplay invariants

These are regression-sensitive systems and require explicit review when touched:

- First Order origin must not receive Xyston/Final Order content at game start; its intended unlock is tied to the Final Order stage.
- Supremacy must retain its ark-ship functionality: population/buildings/modules/ship construction/upgrades and dedicated interface functionality.
- Story-driven fleet restrictions must not globally disable normal player-created fleet merging.
- Global naval-capacity target remains 99999 where the current design applies; command-limit behavior is not to be altered incidentally.
- Leia joining the Rebellion after the civil-war time gate is distinct from the post-Scarif rescue chain; Death Star special-attack/shield-bonus rewards remain tied to the rescue outcome, not merely joining.
- Final Order transition logic must not silently annex the player without the intended war/event transition.

## 6. Models and assets

- Preserve existing UVs, normals, object/material separation and locator semantics when editing imported ship models unless the task explicitly calls for a conversion.
- Validate weapon direction, T/X-slot alignment, fighter locators, engine locators, collision/orientation and relevant VFX/SFX links for model changes.
- Binary assets (`.dds`, `.mesh`, `.anim`, audio) should not be regenerated or recompressed as collateral changes.

## 7. Definition of done

Before a change is considered ready:

1. Read `AGENTS.md`, this file, and `docs/TEST_PLAN.md`.
2. Run `python tools/preflight.py` locally when possible.
3. Perform the relevant automated and manual regression checks.
4. List changed files and explain the behavioral effect.
5. State any untested in-game behavior or remaining risk explicitly.
6. Update `CHANGELOG.md` for player-visible or release-relevant changes.
