#!/usr/bin/env python3
"""Build the client review page (tmp/review/index.html + media/) from the repo's creative.

    python3 scripts/build-review.py

Reads copy/angles.json, video/spots.json, creatives/out/*.png and video/out/*.mp4.
Static ads are converted to JPG for the page; each video gets a poster frame.
"""
import html, json, pathlib, shutil, subprocess
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "tmp/review"
MEDIA = OUT / "media"
copy = json.loads((ROOT / "copy/angles.json").read_text())
spots = {s["id"]: s for s in json.loads((ROOT / "video/spots.json").read_text())["spots"]}
e = html.escape

STATIC = [("meta-1x1", "Meta feed", "1080×1080"), ("meta-4x5", "Meta feed", "1080×1350"), ("meta-9x16", "Stories / Reels", "1080×1920"),
          ("gdn-1.91x1", "Google Display", "1200×628"), ("gdn-1x1", "Google Display", "1200×1200"), ("gdn-4x5", "Google Display", "960×1200")]
VIDEO = [("9x16", "Reels · Stories · Shorts", "1080×1920"), ("4x5", "Meta feed", "1080×1350"), ("16x9", "YouTube · PMax", "1920×1080")]


def build_media():
    if OUT.exists():
        shutil.rmtree(OUT)
    MEDIA.mkdir(parents=True)
    for png in sorted((ROOT / "creatives/out").glob("*.png")):
        im = Image.open(png).convert("RGB")
        im.save(MEDIA / (png.stem + ".jpg"), quality=86, optimize=True)
    for mp4 in sorted((ROOT / "video/out").glob("*.mp4")):
        shutil.copy(mp4, MEDIA / mp4.name)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "5.5", "-i", str(mp4), "-frames:v", "1",
                        "-vf", "scale='min(960,iw)':-2", "-q:v", "4", str(MEDIA / (mp4.stem + "_poster.jpg"))], check=True)
    for srt in sorted((ROOT / "video/out").glob("*.srt")):
        shutil.copy(srt, MEDIA / srt.name)


def probe(mp4):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "json", str(mp4)])
    f = json.loads(out)["format"]
    return float(f["duration"]), int(f["size"]) / 1e6


def chars(s, limit):
    n = len(s)
    return f'<span class="cc{" over" if n > limit else ""}">{n}/{limit}</span>'


def angle_section(a, idx):
    s = spots[a["id"]]
    vids = []
    for sid, where, dim in VIDEO:
        f = ROOT / f"video/out/{a['id']}_{sid}.mp4"
        dur, mb = probe(f)
        vids.append(f'''
        <figure class="vid v{sid}">
          <video controls playsinline preload="none" poster="media/{a['id']}_{sid}_poster.jpg" src="media/{a['id']}_{sid}.mp4"></video>
          <figcaption><b>{where}</b><span class="spec">{dim} · {dur:.1f}s · {mb:.1f} MB</span></figcaption>
        </figure>''')
    statics = "".join(f'''
        <a class="st" href="media/{a['id']}_{sid}.jpg" target="_blank" rel="noopener">
          <img loading="lazy" src="media/{a['id']}_{sid}.jpg" alt="{e(a['name'])}, {where} {dim}">
          <span><b>{where}</b><span class="spec">{dim}</span></span>
        </a>''' for sid, where, dim in STATIC)
    m, g = a["meta"], a["google"]
    gh = "".join(f"<li>{e(h)} {chars(h, 30)}</li>" for h in g["headlines"])
    gd = "".join(f"<li>{e(d)} {chars(d, 90)}</li>" for d in g["descriptions"])
    disc = f'<p class="note">Required disclaimer: {e(copy["legal_payments"])}</p>' if a.get("needs_payment_disclaimer") else ""
    return f'''
  <section class="angle" id="{a['id']}">
    <header class="ahead">
      <p class="eyebrow">Angle {idx} of {len(copy['angles'])}</p>
      <h2>{e(a['name'])}</h2>
      <p class="hook">“{e(a['static']['headline'])}”</p>
    </header>

    <h3>15-second spot</h3>
    <div class="vids">{''.join(vids)}</div>
    <div class="vo">
      <p class="label">Voiceover · Justin Case</p>
      <p>{e(s['vo'])}</p>
      <p class="spec">Captions burned in · <a href="media/{a['id']}.srt" target="_blank" rel="noopener">{a['id']}.srt</a> for YouTube</p>
    </div>

    <h3>Static ads</h3>
    <div class="statics">{statics}</div>

    <h3>Copy</h3>
    <div class="copygrid">
      <div class="copycard">
        <p class="label">Meta · Facebook &amp; Instagram</p>
        <dl>
          <dt>Primary text</dt><dd>{e(m['primary'])} {chars(m['primary'], 125)}</dd>
          <dt>Headline</dt><dd>{e(m['headline'])} {chars(m['headline'], 40)}</dd>
          <dt>Description</dt><dd>{e(m['description'])} {chars(m['description'], 30)}</dd>
          <dt>Button</dt><dd>{e(m['cta_button'])}</dd>
        </dl>
      </div>
      <div class="copycard">
        <p class="label">Google Display · Performance Max</p>
        <dl>
          <dt>Headlines</dt><dd><ul>{gh}</ul></dd>
          <dt>Long headline</dt><dd>{e(g['long_headline'])} {chars(g['long_headline'], 90)}</dd>
          <dt>Descriptions</dt><dd><ul>{gd}</ul></dd>
        </dl>
      </div>
    </div>
    {disc}
  </section>'''


def page():
    angles = copy["angles"]
    nav = "".join(f'<a href="#{a["id"]}">{e(a["name"])}</a>' for a in angles)
    n_vid = len(list((ROOT / "video/out").glob("*.mp4")))
    n_static = len([p for p in (ROOT / "creatives/out").glob("*.png") if not p.stem.startswith("logo")])
    body = "".join(angle_section(a, i + 1) for i, a in enumerate(angles))
    return f'''<title>Flex Payment Creative Review</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="robots" content="noindex, nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Figtree:ital,wght@0,400;0,500;0,700;0,800;0,900;1,800&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: one long review sheet; sticky angle nav; each angle = spot, statics, copy. Brand navy/yellow used as accents only. */
:root {{
  --bg: #fbfbfd; --surface: #ffffff; --fg: #1c1e3a; --muted: #5d6077; --line: #e3e4ee;
  --navy: #262a82; --yellow: #ffdf00; --accent-ink: #262a82; --chip: #eef0fb; --warn: #9a5b00; --warn-bg: #fff6d6;
  --display: "Figtree", "Helvetica Neue", Arial, sans-serif;
  --body: "Figtree", "Helvetica Neue", Arial, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #11132a; --surface: #191c3a; --fg: #eceefb; --muted: #a3a7c6; --line: #2c3058;
  --accent-ink: #c9ccff; --chip: #23275a; --warn: #ffd166; --warn-bg: #3a3315; color-scheme: dark; }} }}
:root[data-theme="dark"] {{
  --bg: #11132a; --surface: #191c3a; --fg: #eceefb; --muted: #a3a7c6; --line: #2c3058;
  --accent-ink: #c9ccff; --chip: #23275a; --warn: #ffd166; --warn-bg: #3a3315; color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{ background: var(--bg); color: var(--fg); font: 16px/1.55 var(--body); }}
.wrap {{ max-width: 1180px; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 0 64px; }}
h1, h2, h3 {{ font-family: var(--display); text-wrap: balance; margin: 0; letter-spacing: -0.02em; }}
a {{ color: var(--accent-ink); }}
a:focus-visible, video:focus-visible {{ outline: 3px solid var(--yellow); outline-offset: 2px; }}
.spec, .cc, .label, .eyebrow {{ font-family: var(--mono); font-size: 12.5px; color: var(--muted); font-variant-numeric: tabular-nums; }}
.label, .eyebrow {{ text-transform: uppercase; letter-spacing: 0.08em; margin: 0 0 8px; }}

/* Masthead */
.mast {{ padding-block: 48px 28px; display: grid; gap: 18px; border-bottom: 1px solid var(--line); }}
.mast h1 {{ font-size: clamp(34px, 6vw, 60px); font-weight: 900; line-height: 1.02; color: var(--fg); }}
.mast h1 em {{ font-style: normal; background: linear-gradient(transparent 62%, var(--yellow) 62%, var(--yellow) 90%, transparent 90%); color: inherit; }}
:root[data-theme="dark"] .mast h1 em {{ color: var(--fg); }}
.mast p.lede {{ max-width: 64ch; margin: 0; color: var(--muted); font-size: 17px; }}
.facts {{ display: flex; flex-wrap: wrap; gap: 10px; margin: 0; padding: 0; list-style: none; }}
.facts li {{ background: var(--chip); border-radius: 999px; padding: 6px 14px; font-weight: 700; font-size: 14px; }}
.facts li span {{ font-family: var(--mono); font-weight: 500; color: var(--muted); margin-left: 6px; }}

/* Sticky angle nav */
body::before {{ content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px); z-index: 10; background: var(--bg); }}
nav.angles {{ position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5; background: var(--bg); border-bottom: 1px solid var(--line);
  display: flex; gap: 6px; overflow-x: auto; padding-block: 10px; scrollbar-width: none; }}
nav.angles a {{ flex: none; text-decoration: none; color: var(--fg); font-weight: 700; font-size: 14px; padding: 6px 12px; border-radius: 999px; }}
nav.angles a:hover {{ background: var(--chip); }}

/* Brand direction */
.direction {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 28px; padding-block: 36px; border-bottom: 1px solid var(--line); }}
.direction h3 {{ font-size: 15px; margin-bottom: 10px; }}
.swatches {{ display: flex; gap: 8px; flex-wrap: wrap; }}
.sw {{ display: grid; gap: 4px; font-family: var(--mono); font-size: 11.5px; color: var(--muted); }}
.sw i {{ display: block; width: 54px; height: 40px; border-radius: 6px; border: 1px solid var(--line); }}
.direction ul {{ margin: 0; padding-left: 18px; color: var(--muted); }}
.direction li {{ margin-bottom: 4px; }}

/* Angle */
.angle {{ padding-block: 48px 8px; border-bottom: 1px solid var(--line); scroll-margin-top: 64px; display: grid; gap: 18px; }}
.ahead h2 {{ font-size: clamp(28px, 4vw, 40px); font-weight: 900; color: var(--accent-ink); }}
.hook {{ margin: 6px 0 0; font-size: 19px; font-weight: 700; }}
.angle h3 {{ font-size: 18px; font-weight: 800; margin-top: 14px; }}
.vids {{ display: grid; grid-template-columns: 0.75fr 1fr 1.9fr; gap: 16px; align-items: end; }}
.vid {{ margin: 0; display: grid; gap: 8px; min-width: 0; }}
.vid video {{ width: 100%; max-width: 100%; display: block; border-radius: 10px; background: #000; border: 1px solid var(--line); }}
.v9x16 video {{ aspect-ratio: 9 / 16; }} .v4x5 video {{ aspect-ratio: 4 / 5; }} .v16x9 video {{ aspect-ratio: 16 / 9; }}
.vid figcaption {{ display: flex; flex-direction: column; font-size: 14px; }}
.vo {{ background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 16px 18px; max-width: 78ch; }}
.vo p {{ margin: 0 0 6px; }}
.statics {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 14px; align-items: end; }}
.st {{ display: grid; gap: 6px; text-decoration: none; color: var(--fg); min-width: 0; }}
.st img {{ width: 100%; height: auto; border-radius: 6px; border: 1px solid var(--line); background: #fff; }}
.st:hover img {{ border-color: var(--accent-ink); }}
.st > span {{ display: flex; flex-direction: column; font-size: 13px; }}
.copygrid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
.copycard {{ background: var(--surface); border: 1px solid var(--line); border-radius: 12px; padding: 16px 18px; min-width: 0; }}
dl {{ margin: 0; display: grid; grid-template-columns: 120px 1fr; gap: 8px 14px; }}
dt {{ font-weight: 700; font-size: 14px; }}
dd {{ margin: 0; min-width: 0; }}
dd ul {{ margin: 0; padding-left: 18px; }}
.cc {{ white-space: nowrap; margin-left: 4px; }}
.cc.over {{ color: #c62828; font-weight: 600; }}
.note {{ background: var(--warn-bg); color: var(--warn); border-radius: 8px; padding: 10px 14px; margin: 0; font-size: 14px; }}

/* Open items */
.open {{ padding-block: 40px 0; display: grid; gap: 14px; }}
.open ol {{ margin: 0; padding-left: 22px; display: grid; gap: 10px; max-width: 80ch; }}
.legal {{ color: var(--muted); font-size: 13px; max-width: 90ch; margin-top: 28px; }}

@media (max-width: 860px) {{
  .vids {{ grid-template-columns: 1fr 1fr; }} .v16x9 {{ grid-column: 1 / -1; }}
  .statics {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }}
  .copygrid {{ grid-template-columns: 1fr; }}
}}
@media (max-width: 480px) {{
  .statics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  dl {{ grid-template-columns: 1fr; gap: 2px; }} dd {{ margin-bottom: 8px; }}
}}
@media (prefers-reduced-motion: reduce) {{ html {{ scroll-behavior: auto; }} }}
html {{ scroll-behavior: smooth; }}
</style>

<div class="wrap">
  <header class="mast">
    <p class="eyebrow">Guild Mortgage · Flex Payment Mortgage · Round 1 review · Nov 15, 2026</p>
    <h1>Your mortgage, <em>your way.</em><br>Paid social &amp; display creative</h1>
    <p class="lede">Five message angles drawn from flexpaymentmortgage.com, each as a 15-second motion spot, six static sizes and platform copy. Please review each angle and leave comments on anything you'd change.</p>
    <ul class="facts">
      <li>{len(angles)} angles</li>
      <li>{n_vid} videos<span>15s · 30fps · −14 LUFS</span></li>
      <li>{n_static} static ads<span>+ 2 logo assets</span></li>
      <li>Meta + Google Display<span>copy within limits</span></li>
    </ul>
  </header>

  <nav class="angles" aria-label="Angles">{nav}<a href="#open-items">Open items</a></nav>

  <section class="direction" aria-label="Brand direction">
    <div>
      <h3>Palette</h3>
      <div class="swatches">
        <span class="sw"><i style="background:#262a82"></i>#262A82</span>
        <span class="sw"><i style="background:#ffdf00"></i>#FFDF00</span>
        <span class="sw"><i style="background:#00b5ef"></i>#00B5EF</span>
        <span class="sw"><i style="background:#4a494a"></i>#4A494A</span>
        <span class="sw"><i style="background:#f7f7f7"></i>#F7F7F7</span>
      </div>
    </div>
    <div>
      <h3>Voice</h3>
      <ul>
        <li>Warm, plain-spoken, reassuring. We sell flexibility, not debt.</li>
        <li>“Reverse mortgage” stays out of headlines, as on the site.</li>
        <li>No age call-outs (Meta special ad category: financial products).</li>
      </ul>
    </div>
    <div>
      <h3>Motion &amp; sound</h3>
      <ul>
        <li>Yellow triangle reveal, cyan “Flex” arrow transitions, logo end card.</li>
        <li>Voiceover: Justin Case (ElevenLabs). Acoustic music bed, ducked under the voice.</li>
        <li>9:16 text kept inside the Reels safe zone.</li>
      </ul>
    </div>
  </section>

  {body}

  <section class="open" id="open-items">
    <h2>Open items</h2>
    <ol>
      <li><b>Photography license.</b> The lifestyle photos come from flexpaymentmortgage.com. Please confirm they're licensed for paid media, or share approved stock. Only the beach photo is high-resolution; the others look soft at video sizes.</li>
      <li><b>Brand font.</b> The site uses Circular Std. These drafts use Figtree, a close match. If you can share licensed Circular files, we'll swap them in.</li>
      <li><b>Compliance review.</b> End cards and static footers carry NMLS #3274, Equal Housing Opportunity and underwriter-approval language. The payment-freedom angle adds the taxes, insurance and upkeep disclaimer. Please route through your compliance team.</li>
      <li><b>Home-upgrades visuals.</b> This angle reuses the beach photo. Interior or home photography would fit the message better.</li>
    </ol>
    <p class="legal">Draft creative for client review only; not for distribution. {e(copy['legal_short'])}</p>
  </section>
</div>
'''


if __name__ == "__main__":
    build_media()
    (OUT / "index.html").write_text(page().encode("ascii", "xmlcharrefreplace").decode())
    total = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file()) / 1e6
    print(f"wrote {OUT/'index.html'}  ({len(list(MEDIA.iterdir()))} media files, {total:.1f} MB)")
