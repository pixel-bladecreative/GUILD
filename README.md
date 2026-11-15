# GUILD: Flex Payment Mortgage ad creative

Paid-social and display creative for Guild Mortgage's reverse-mortgage brand, **Flex Payment Mortgage** (flexpaymentmortgage.com).

| Folder | What |
|---|---|
| `brand/` | Brand guide (voice, colors, type, photo direction, compliance), tokens CSS, logo, photos, fonts |
| `copy/` | `angles.json`, the single source of ad copy. `meta.md` and `google-display.md` are generated from it |
| `creatives/` | Static ad template (`ad.html`) plus rendered PNGs in `creatives/out/` |
| `video/` | 15s motion-graphics spots: `scripts.md`, `spots.json` (timeline spec), `spot.html` (GSAP), renders in `video/out/` |
| `scripts/` | Build and render scripts |

## Build

```bash
npm install
```

```bash
python3 scripts/build_copy.py          # validate copy limits and regenerate copy/*.md
```

```bash
node scripts/render-static.js          # all static ads to creatives/out/
```

```bash
node scripts/render-video.js all all --stills   # quick contact-sheet frames to tmp/stills/
```

```bash
node scripts/render-video.js all all            # 15 MP4s (5 spots x 9:16, 4:5, 16:9), silent
```

```bash
node scripts/render-video.js all all --audio    # mux video/audio/<spot>.mix.wav when present
```

To preview a spot live in a browser, serve the repo root and open `video/spot.html?spot=brand&w=1080&h=1920&play=1`.

## Sizes

- **Static:** Meta 1080×1080, 1080×1350, 1080×1920 · Google Display 1200×628, 1200×1200, 960×1200 · logos 1200×1200, 1200×300
- **Video:** 1080×1920 (Reels/Stories/Shorts), 1080×1350 (feed), 1920×1080 (YouTube/PMax). 30fps H.264 + AAC, 15.0s

## Open items

- The Guild font (Circular Std) isn't licensed here; Figtree substitutes for it.
- Site photos: check the usage license. Only the hero is high-resolution.
- Voiceover and music are pending script approval (`video/scripts.md`).
