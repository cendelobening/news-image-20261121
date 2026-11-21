[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/cendelobening/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/cendelobening/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

# THE WORLD — Saturday 21 November 2026

A one-page newspaper front page summing up Saturday 21 November 2026 world
news, drawn entirely by a pure-stdlib Python generator (`gen.py`): navy
masthead, red date band, one big lead story, five more stories in a grid,
and a bottom strip with a seventh story. The letters come from a hand-built
5x7 bitmap font and the PNG is encoded with `struct` + `zlib` only — no
Pillow, no numpy, no other packages.

Bounty: https://make.fun/bounty/news-image-20261121

## The six stories

1. **Russian missiles cross into Poland** — missiles and drones cross Polish
   territory; a detonation triggers an airspace-incursion probe and NATO
   allies respond.
2. **Kryvyi Rih strike kills 2, wounds 42** — a Russian strike kills two
   people and injures 42, including four children.
3. **Cyclone Akvan crosses Odisha coast** — the cyclone crosses the Odisha
   and Andhra coast near Gopalpur, with strong winds and heavy rain.
4. **Banks hit in cyberattack** — JPMorgan, Visa and Mastercard report a
   cyberattack on third-party vendors; core networks are unaffected.
5. **COP31 enters final stage** — UN climate talks in Turkey reach their
   crucial final phase; fossil-fuel use and climate finance are the
   sticking points.
6. **2027 Elantra debuts** — Hyundai unveils the eighth-generation Elantra
   at the Los Angeles Auto Show, with a redesigned exterior and hybrid
   options.

Bottom strip: Estonia to close Russia border crossings from 1 December.

## Run

```sh
python3 gen.py
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

`gen.py` writes a deterministic 1024x1024 8-bit RGB `entry.png` (under
1 MiB). `main.py` validates the PNG (signature, IHDR first, dimensions,
bit depth, colour type, chunk CRCs, exact decoded scanlines) and copies it
byte-for-byte to `$MAKEFUN_OUTPUT_DIR/entry.png` with mode 0644.
