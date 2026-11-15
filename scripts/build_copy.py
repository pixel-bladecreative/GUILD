#!/usr/bin/env python3
"""Validate ad copy in copy/angles.json against platform limits and write copy/*.md."""
import json, sys, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
data = json.loads((root / "copy/angles.json").read_text())
LIM = {"meta.primary": 125, "meta.headline": 40, "meta.description": 30,
       "google.headline": 30, "google.long_headline": 90, "google.description": 90, "business_name": 25}
BANNED = ["free money", "tax-free", "62", "never pay", "seniors", "elderly"]
errors = []
def chk(label, text, key):
    if len(text) > LIM[key]:
        errors.append(f"{label}: {len(text)}>{LIM[key]} chars: {text!r}")
    for b in BANNED:
        if b in text.lower():
            errors.append(f"{label}: banned phrase {b!r}: {text!r}")
chk("business_name", data["business_name"], "business_name")
meta, goog = ["# Meta (Facebook / Instagram) ad copy\n",
    "Special Ad Category: **Financial products & services**. Destination: " + data["url"] + "\n"], \
    ["# Google Display / Performance Max copy\n", f"Business name: **{data['business_name']}**\n"]
for a in data["angles"]:
    m, g, i = a["meta"], a["google"], a["id"]
    chk(f"{i}.meta.primary", m["primary"], "meta.primary")
    chk(f"{i}.meta.headline", m["headline"], "meta.headline")
    chk(f"{i}.meta.description", m["description"], "meta.description")
    for n, h in enumerate(g["headlines"]): chk(f"{i}.google.h{n}", h, "google.headline")
    chk(f"{i}.google.long", g["long_headline"], "google.long_headline")
    for n, d in enumerate(g["descriptions"]): chk(f"{i}.google.d{n}", d, "google.description")
    disc = f"\n*Disclaimer required:* {data['legal_payments']}\n" if a["needs_payment_disclaimer"] else ""
    meta.append(f"\n## {a['name']} (`{i}`)\n\n| Field | Copy | Chars |\n|---|---|---|\n"
        f"| Primary text | {m['primary']} | {len(m['primary'])} |\n| Headline | {m['headline']} | {len(m['headline'])} |\n"
        f"| Description | {m['description']} | {len(m['description'])} |\n| CTA button | {m['cta_button']} | |\n{disc}")
    rows = "".join(f"| Headline {n+1} | {h} | {len(h)} |\n" for n, h in enumerate(g["headlines"]))
    rows += f"| Long headline | {g['long_headline']} | {len(g['long_headline'])} |\n"
    rows += "".join(f"| Description {n+1} | {d} | {len(d)} |\n" for n, d in enumerate(g["descriptions"]))
    goog.append(f"\n## {a['name']} (`{i}`)\n\n| Field | Copy | Chars |\n|---|---|---|\n{rows}{disc}")
footer = f"\n---\nLegal (on creative): {data['legal_short']}\n"
(root / "copy/meta.md").write_text("".join(meta) + footer)
(root / "copy/google-display.md").write_text("".join(goog) + footer)
if errors:
    print("\n".join(errors)); sys.exit(1)
print(f"OK: {len(data['angles'])} angles within limits; wrote copy/meta.md, copy/google-display.md")
