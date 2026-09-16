# Changelog

All notable player-visible and release-relevant changes to Star Wars Fall of the Republic should be recorded here.

## Unreleased

### Fixes awaiting in-game acceptance
- Native Imperial/First Order revolt countries are identified by their exact parent-country flag, not by their current origin or war status.
- Added independent monthly/save-load recovery, validated Rebel-recipient fallback, and player/story-country safeguards. Final Order and unrelated foreign countries are excluded.
- Preserved ordinary fleets and territory without spawning repeat reinforcements. Added focused static/policy regression tests; runtime acceptance remains required.

### Engineering
- Added repository engineering rules, AI/Codex working contract, regression test plan, static preflight checker, GitHub Actions audit workflow, `.gitattributes`, and `.gitignore`.
