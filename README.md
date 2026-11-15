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

### Audio

Music bed: SunoBoard "Open Doors" take A (`video/audio/src/music_a.mp3`), from 0–15s; it lifts at about 9.5s to meet the brand panel. Voiceover: ElevenLabs "Justin Case" on `eleven_v4`. Save the chosen takes as `video/audio/vo/<spot>.mp3`.

```bash
scripts/mix-audio.sh                    # duck music under VO, -14 LUFS, remux onto video/out/*.mp4 (no re-render)
```

```bash
python3 scripts/align-captions.py       # retime captions in spots.json to the real VO and write video/out/<spot>.srt
```

```bash
node scripts/render-video.js all all && scripts/mix-audio.sh   # re-render with the new caption timing, then remux audio
```

To preview a spot live in a browser, serve the repo root and open `video/spot.html?spot=brand&w=1080&h=1920&play=1`.

## Sizes

- **Static:** Meta 1080×1080, 1080×1350, 1080×1920 · Google Display 1200×628, 1200×1200, 960×1200 · logos 1200×1200, 1200×300
- **Video:** 1080×1920 (Reels/Stories/Shorts), 1080×1350 (feed), 1920×1080 (YouTube/PMax). 30fps H.264 + AAC, 15.0s

## Open items

- The Guild font (Circular Std) isn't licensed here; Figtree substitutes for it.
- Site photos: check the usage license. Only the hero is high-resolution.
- Voiceover is blocked: the ElevenLabs account has a failed or incomplete payment. Videos currently carry the music bed only.
