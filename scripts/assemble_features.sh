#!/usr/bin/env bash
# Processes the raw features recording into two captioned segments,
# then concatenates them into astronomus-features.mp4.
#
# Input:  astronomus-features-raw.mp4
# Output: astronomus-features.mp4
#
# Segment timing in the raw recording (from record_features.js sleeps):
#   0–14s  : Local Weather + Observability (Tonight home page)
#   14–26s : Satellite Avoidance checkbox (Plan constraints panel)
#
# Adjust these offsets if your actual recording runs faster/slower:
WEATHER_START=0
WEATHER_DUR=11
SAT_START=11
SAT_DUR=10

set -euo pipefail

SRC="astronomus-features-raw.mp4"
OUT="astronomus-features.mp4"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

if [[ ! -f "$SRC" ]]; then
  echo "ERROR: $SRC not found. Run: node scripts/record_features.js first."
  exit 1
fi

ACTUAL_DUR=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$SRC")
echo "Raw features duration: ${ACTUAL_DUR}s"

echo "Step 1/3: Extracting and captioning local weather segment..."
ffmpeg -y -ss "$WEATHER_START" -t "$WEATHER_DUR" -i "$SRC" \
  -vf "
    fade=t=in:st=0:d=0.5,
    fade=t=out:st=$((WEATHER_DUR-1)):d=0.8,

    drawtext=fontfile='$FONT':
      text='Local Weather Station':
      fontcolor=0x22d3ee:fontsize=20:
      x=24:y=24:
      box=1:boxcolor=black@0.6:boxborderw=6,

    drawtext=fontfile='$FONT_REG':
      text='Live conditions from your Ambient Weather WS-2902 — observability score updated every minute':
      fontcolor=white:fontsize=21:
      x=30:y=h-70:
      box=1:boxcolor=black@0.55:boxborderw=8:
      enable='between(t,1,$((WEATHER_DUR-1)))'
  " \
  -c:v libx264 -crf 17 -preset slow /tmp/feat_weather.mp4 2>/dev/null

echo "Step 2/3: Extracting and captioning satellite avoidance segment..."
ffmpeg -y -ss "$SAT_START" -t "$SAT_DUR" -i "$SRC" \
  -vf "
    fade=t=in:st=0:d=0.5,
    fade=t=out:st=$((SAT_DUR-1)):d=0.8,

    drawtext=fontfile='$FONT':
      text='Satellite Avoidance':
      fontcolor=0xf87171:fontsize=20:
      x=24:y=24:
      box=1:boxcolor=black@0.6:boxborderw=6,

    drawtext=fontfile='$FONT_REG':
      text='Pulls Celestrak TLEs — imaging slots blocked automatically when a pass is predicted':
      fontcolor=white:fontsize=21:
      x=30:y=h-70:
      box=1:boxcolor=black@0.55:boxborderw=8:
      enable='between(t,1,$((SAT_DUR-1)))'
  " \
  -c:v libx264 -crf 17 -preset slow /tmp/feat_satellite.mp4 2>/dev/null

echo "Step 3/3: Concatenating feature segments..."
cat > /tmp/feat_concat.txt << 'CONCAT'
file '/tmp/feat_weather.mp4'
file '/tmp/feat_satellite.mp4'
CONCAT

ffmpeg -y -f concat -safe 0 -i /tmp/feat_concat.txt \
  -c:v libx264 -crf 17 -preset slow \
  "$OUT" 2>/dev/null

echo ""
echo "Done! → $OUT"
ffprobe -v quiet -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUT"
