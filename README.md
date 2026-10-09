# Critters

A collector's game of 60 original crypto critters: open 17 kinds of packs across 7 rarities, fill the book, level up a buddy in 8 minigames, and battle trainers in the Arena. One self-contained `index.html`, no build step, no dependencies.

All critters, names and art are original. Coins are play money with no cash value, and nothing in the page sends or signs a transaction (the wallet button only displays a public address).

## Play it locally
Open `index.html` in a browser.

## Put it online (GitHub Pages)
Push to GitHub, then **Settings, Pages, Source: GitHub Actions**. `.github/workflows/pages.yml` publishes the site at `https://<you>.github.io/<repo>/`.

## What's in it
- **Packs:** daily (free), starter, premium, mega, one pack per type, and elite packs, plus the Arcade Pack (10 tickets from minigames). Odds and guarantees are shown on each pack. No pack can refund more coins in duplicates than it costs.
- **Collection:** 60 critters, Common to Genesis, shinies, silhouettes until found, filters.
- **Minigames (8):** Wild Catch, Meadow Run, Berry Blitz, Burrow Bash, Critter Beats, Who is That, Type Master, Berry Memory. Stars, high scores, buddy XP, tickets, a daily bonus game, 12 trophies.
- **Arena:** five trainers plus sparring, items and shop, levels and XP, moves with effects, Stunned and Rugged statuses, a passive per type, type-specific attack animations.
- **Extras:** an interactive night-meadow background, hero cards that switch on hover, read-only wallet display.

## Tests
```
pip install playwright pillow
python3 -m playwright install chromium
cd tests
python3 ct1.py   # data, art, packs, book, hero, background (119 checks)
python3 ct2.py   # header, X button, logo, meadow interactions (62)
python3 ct3.py   # progression and minigame logic (68)
python3 ct4.py   # battle engine (79)
python3 ct5.py   # Arena screens and animations (51)
python3 ct6.py   # all 8 minigames, intro to results (51)
```
Each prints PASS/FAIL lines and a SUMMARY. They run against `../index.html`.

## Docs
- `docs/ARCHITECTURE.md` how the single file is organised and the test hooks
- `docs/GAME_DESIGN.md` rarities, odds, economy limits, battle rules, minigame rewards

## Swapping in your own art
Each critter is a row in the `ROSTER` list at the top of the script. Add an `img` field (an image address or data URI) to replace a drawing with your own image. Anything you add yourself is your responsibility.
