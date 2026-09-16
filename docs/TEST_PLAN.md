# FOC Regression Test Plan

This document separates automated static checks from in-game acceptance tests. When a PR touches one of these systems, the matching checks are mandatory.

## A. Automated preflight

Run `python tools/preflight.py` before review.

The preflight currently checks:

- UTF-8 decoding for text assets;
- BOM policy (localisation `.yml` requires BOM; ordinary text files must not have BOM);
- basic brace balance outside quoted strings/comments;
- duplicate Stellaris event IDs (`id = namespace.number` style);
- duplicate localisation keys inside localisation files;
- scripted-effect call graph depth and direct/mutual recursion where detectable.

Legacy repository-wide findings can initially be audited with `--report-only`. New PRs should not introduce additional findings.

## B. Core fleet regressions

- Republic player starting fleets are recognized as real fleets, can move, merge and disband where intended.
- Player-controlled opening fleets for other factions remain movable/mergeable unless a specific story restriction says otherwise.
- Imperial Rebel garrison fleets remain in their intended systems and are not teleported back to a rebel capital.
- Republic -> Imperial Rebel transition does not create recurring fleets containing only two MC80s.
- Story-fleet restrictions do not disable merging of normal player-built fleets.
- Home One spawns in an Imperial Rebel system without an Imperial fleet, according to current design.

## C. Clone Wars / Republic-origin regressions

- Clone Wars events do not display obsolete victory-condition text.
- Separatists do not surrender prematurely from unrelated event-chain state.
- Republic-origin war result is driven by the intended total-war outcome logic.
- Order 66 / transition events still fire from the intended trigger chain.
- Republic starting assets remain valid through faction conversion.

## D. Galactic Civil War / Leia / Scarif

- Scarif cannot trigger before its required prerequisites.
- "Leia and Alderaan" cannot trigger until at least the configured post-Scarif delay.
- Leia joining after 10 years of actual Galactic Civil War is a separate event from Leia being rescued.
- Leia joining alone does not grant the Death Star special attack or shield-damage bonus.
- Rescue outcome grants only the intended bonuses once.
- Death Star I / II destruction events and the final redemption chain do not duplicate or skip required deaths/outcomes.

## E. First Order / Final Order

- First Order origin starts without Xyston access.
- Resurgent and other intended First Order content unlock at the correct stage.
- Xyston unlocks only with the Final Order stage.
- Final Order transition does not silently annex the player; intended war/event logic occurs.
- Difficulty-tier variants preserve the intended lowest-tier / vanilla-balance behavior.
- No unintended Eclipse II or equivalent end-stage ship is buildable at game start.

## F. Ships / weapons / special hulls

- Supremacy keeps ark-ship population, buildings, modules, shipbuilding, upgrades and dedicated UI functionality.
- Executor, Eclipse, Viscount, Resurgent, Nebula, Imperial I/II and Xyston keep their intended section/slot layouts.
- Imperial weapon visuals remain green and Rebel weapon visuals red where the faction weapon families specify this.
- T-slot superweapons retain their intended resource costs and cannot be equipped by unintended hulls.
- Xyston T weapon still applies the intended shield debuff.
- Fighter/strike-craft changes do not replace unrelated existing craft unless explicitly requested.

## G. Resources / compatibility

- FOC launches and plays without SG enabled.
- With SG enabled, only the intended shared resource inventory/IDs are shared; SG components/technologies/events/buildings/economy logic are not overwritten by FOC compatibility code.
- Coaxium and Beskar FOC definitions remain available where required.
- Kessel/Mandalore resource production remains at intended values after map/event changes.

## H. Models and presentation

For any imported/edited model:

- scale is plausible relative to the formation;
- orientation and collision are correct;
- weapon locators fire in the correct direction;
- T-slot alignment is correct;
- strike-craft/engine/light locators are valid;
- textures/materials/UVs are intact;
- no unrelated binary asset was regenerated.

## I. Release smoke test

Before tagging a release:

1. clean game launch with FOC only;
2. new-game load for major playable origins/factions touched by the release;
3. no new FOC parser/error-log flood during first month;
4. one save/reload cycle;
5. exercise at least one modified event/technology/ship path;
6. confirm descriptor version and Workshop packaging contents.
