#!/usr/bin/env python3
"""Retime each spot's captions to its actual voiceover and write SRT files.

    python3 scripts/align-captions.py [spotId ...]

Detects speech segments in video/audio/vo/<spot>.(wav|mp3) with ffmpeg silencedetect,
then distributes the caption chunks across speech time in proportion to their
character counts (chunks snap to pauses when they line up). Updates the
"captions" timings in video/spots.json and writes video/out/<spot>.srt.
Re-render the video afterwards so the burned-in captions use the new timing.
"""
import json, os, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
VO_DELAY = float(os.environ.get("VO_DELAY_MS", 250)) / 1000
DUR = 15.0


def speech_segments(path):
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", str(path)]).decode())
    log = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
                          "silencedetect=n=-35dB:d=0.18", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    segs, cur = [], 0.0
    for s, e in zip(starts, ends + [dur] * (len(starts) - len(ends))):
        if s > cur + 0.05:
            segs.append((cur, s))
        cur = e
    if cur < dur - 0.05:
        segs.append((cur, dur))
    return segs, dur


def to_real(segs, speech_t):
    """Map cumulative speech time to real time."""
    acc = 0.0
    for a, b in segs:
        if speech_t <= acc + (b - a) + 1e-6:
            return a + (speech_t - acc)
        acc += b - a
    return segs[-1][1]


def snap(t, segs, which, tol=0.25):
    edges = [a for a, _ in segs] if which == "start" else [b for _, b in segs]
    best = min(edges, key=lambda e: abs(e - t))
    return best if abs(best - t) <= tol else t


def fmt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main():
    cfg_path = ROOT / "video/spots.json"
    cfg = json.loads(cfg_path.read_text())
    want = set(sys.argv[1:])
    (ROOT / "video/out").mkdir(parents=True, exist_ok=True)
    for spot in cfg["spots"]:
        if want and spot["id"] not in want:
            continue
        vo = next((p for p in [ROOT / f"video/audio/vo/{spot['id']}.{e}" for e in ("wav", "mp3")] if p.exists()), None)
        if not vo:
            print(f"skip {spot['id']}: no voiceover")
            continue
        segs, dur = speech_segments(vo)
        if dur + VO_DELAY > DUR - 0.3:
            print(f"WARNING {spot['id']}: VO is {dur:.2f}s; too long for a {DUR:.0f}s spot")
        total_speech = sum(b - a for a, b in segs)
        chars = [len(c[2]) for c in spot["captions"]]
        total_chars = sum(chars)
        acc, new = 0, []
        for (_, _, text), n in zip(spot["captions"], chars):
            s = snap(to_real(segs, total_speech * acc / total_chars), segs, "start")
            acc += n
            e = snap(to_real(segs, total_speech * acc / total_chars), segs, "end")
            new.append([round(s + VO_DELAY, 2), round(min(e + VO_DELAY + 0.15, DUR - 0.05), 2), text])
        for i in range(len(new) - 1):  # no overlaps
            new[i][1] = round(min(new[i][1], new[i + 1][0] - 0.02), 2)
        spot["captions"] = new
        srt = "\n".join(f"{i + 1}\n{fmt(a)} --> {fmt(b)}\n{t}\n" for i, (a, b, t) in enumerate(new))
        (ROOT / f"video/out/{spot['id']}.srt").write_text(srt)
        print(f"aligned {spot['id']}: VO {dur:.2f}s, {len(segs)} speech segments")
    cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
