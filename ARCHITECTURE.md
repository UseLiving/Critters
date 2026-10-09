# Architecture

Everything is in `index.html` (HTML, CSS, one `<script>` wrapped in an IIFE). Script sections in order:

1. **data**: `TYPES`, `STRONG` (the type chart), `RAR`, `ROSTER` (60 rows).
2. **art**: `art(critter, shiny)` draws every critter as an SVG from its data (aura, gear, patterns, rarity effects). Each call gets unique gradient ids.
3. **core**: state `S` and its sanitised `load()`/`save()` (localStorage key `critterchain_v1`), sound (`SND`, `sfx`), packs (`PK`, `rollPack`, `grant`, `openPack`), levels (`lvMult`, `giveXP`), buddy, tickets, daily `featured()`, trophies (`ACH`, `checkAch`), shared minigame rewards `mgFinish`.
4. **ui**: cards, stage (modal) helpers, pack shop and reveal, collection book, buddy panel, trophies.
5. **minigames** (`mg_a/b/c` in the source): shared shell `mgOpen`/`mgResult`, then one function per game plus pure logic functions (`runStep`, `bbPlay`, `bashHit`, `beatPress`, `quizQ`, ...).
6. **battle**: engine (`newBattle`, `resolveTurn`, `doMove`, `movesFor`, `fighter`, `dmgCalc`, items, rounds). Pure state, events list for the UI.
7. **battle UI**: `arena()` menu and `battleScreen()` scene, command menus, `fx()` attack animations.
8. **wallet**: read-only (`connect`, `useAddr`).
9. **background** `BGM` (two canvases: still sky and a small animated grass strip, plus DOM stars/rings) and **hero** (`HERO`).
10. **start** and `window.__cc` (test hooks).

## Rules for contributors
- Never add code that signs or sends transactions or handles keys.
- Keep randomness behind `rnd()` (tests replace `window.__rnd`) and time behind `now()` (`window.__fakeNow`).
- Battle logic must stay free of DOM access; the UI plays `B.events`.
- Set `window.__fast = true` to skip battle delays in tests.
- Respect `prefers-reduced-motion` and keep text contrast (the tests audit it).
- Run all six suites before merging.
