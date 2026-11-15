#!/usr/bin/env bash
# Build per-spot audio mixes and remux them onto rendered videos.
#
#   scripts/mix-audio.sh            # mix every spot, remux onto video/out/*.mp4
#
# Inputs:
#   video/audio/src/music_a.mp3     music bed source (SunoBoard, "Open Doors" take A)
#   video/audio/vo/<spot>.mp3|wav   voiceover (optional; music-only mix if missing)
# Outputs:
#   video/audio/<spot>.mix.wav      15.0s, 48k stereo, ~-14 LUFS
#   video/out/<spot>_<size>.mp4     audio track replaced (video stream copied, no re-render)
set -euo pipefail
cd "$(dirname "$0")/.."
DUR=15
BED_START=${BED_START:-0}       # where in the music track the bed starts (s)
VO_DELAY_MS=${VO_DELAY_MS:-250} # VO starts slightly after picture
mkdir -p video/audio tmp/audio

# 1. Music bed: 15s cut with a quick fade-in and a 1.2s fade-out
ffmpeg -y -loglevel error -ss "$BED_START" -t "$DUR" -i video/audio/src/music_a.mp3 \
  -af "afade=t=in:d=0.05,afade=t=out:st=13.8:d=1.2,aresample=48000" -ac 2 tmp/audio/bed.wav

for spot in $(python3 -c "import json;print(' '.join(s['id'] for s in json.load(open('video/spots.json'))['spots']))"); do
  vo=$(ls video/audio/vo/${spot}.{wav,mp3} 2>/dev/null | head -1 || true)
  out=video/audio/${spot}.mix.wav
  if [[ -n "$vo" ]]; then
    # Voiceover over the bed, with the music ducked under the voice (sidechain compression), then loudness-normalized
    ffmpeg -y -loglevel error -i tmp/audio/bed.wav -i "$vo" -filter_complex "
      [1:a]aresample=48000,aformat=channel_layouts=stereo,adelay=${VO_DELAY_MS}|${VO_DELAY_MS},loudnorm=I=-16:TP=-2:LRA=7,aresample=48000,apad=whole_dur=${DUR}[vo];
      [vo]asplit=2[vo1][vo2];
      [0:a]volume=-6dB[bed];
      [bed][vo2]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400:makeup=1[duck];
      [duck][vo1]amix=inputs=2:normalize=0,atrim=0:${DUR},loudnorm=I=-14:TP=-1.5:LRA=9[out]" \
      -map "[out]" -ar 48000 -ac 2 "$out"
    echo "mixed $spot (VO + music)"
  else
    ffmpeg -y -loglevel error -i tmp/audio/bed.wav -af "loudnorm=I=-16:TP=-1.5:LRA=9" -ar 48000 -ac 2 "$out"
    echo "mixed $spot (music only; no VO found)"
  fi
  # Remux onto every rendered size without re-encoding video
  for v in video/out/${spot}_*.mp4; do
    [[ -e "$v" ]] || continue
    ffmpeg -y -loglevel error -i "$v" -i "$out" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 \
      -t "$DUR" -movflags +faststart tmp/audio/remux.mp4 && mv tmp/audio/remux.mp4 "$v"
  done
done
