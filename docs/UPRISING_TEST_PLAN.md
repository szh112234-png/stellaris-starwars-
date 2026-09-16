# Imperial uprising annexation regression plan

Baseline: v17.18o, b9cf3c10f2cf282fa92f7642cd31ae6078967b8c.
The inherited helper required Republic story event .140, an active civil-war flag,
valid global targets, origin_separatists, and a current formal war. The new scan
requires the exact native separatist_rebel_of_@<Imperial/First Order parent> flag
instead. Origin changes and peace do not establish or invalidate provenance.

## Automated

Run `python tools/test_uprising_annexation.py` and `python tools/preflight.py`.
Existing preflight findings are baseline findings, not proof of game failures;
compare individual findings, not only totals. These tests are static/policy checks,
not a Stellaris runtime emulator.

## Required in-game acceptance (not yet performed)

- Empire revolt while at war: after at most one monthly pulse, territory and normal
  fleets join the correct Rebels; no replacement MC80 fleet/reward is generated.
- Empire permits independence/truce: the same native revolt still joins Rebels.
- Already-spawned native revolt: load an old save and advance a month; no new game
  is needed if the native parent flag and eligible parent still exist.
- Void-dweller/necrophage revolt whose origin is rewritten: provenance still works.
- AI Empire and Rebel player/AI routes: no Republic-player-only gate remains.
- First Order parent permitted; Final Order parent excluded even with old flags.
- Unrelated third-country revolt at war with the Empire: remains independent.
- Republic/CIS/New Republic/Remnant/Mandalore/Hutt countries and human-controlled
  breakaways must not be absorbed.
- Missing/stale canonical Rebel target: a unique valid Rebel faction is found.
  No recipient, or multiple candidates without a valid canonical target: no annex.
- Two simultaneous revolts: no target cross-talk; save/reload does not repeat rewards.
- Population/buildings, starbases, normal fleets and defensive armies survive the
  ownership transfer. Temporary SSP strike sorties are not inherited.
- Check currently occupied planets, war termination, starbase ownership, habitats
  and third-party compatibility before release. Runtime ownership behavior and
  global superweapon state have not been validated by the static test.

Look for `FOC_UPRISING_ANNEX` in game.log. If no native provenance survives (e.g.
a different mod creates the country without it, or the original parent is gone),
this fix deliberately does not guess based on country name, origin or enemies.
Provide the save and logs to investigate that case instead of using broad annex.
