#!/usr/bin/env bash
# Assembles astronomus-demo.mp4 into a polished LinkedIn video.
# Music: Kevin MacLeod — "Slow Burn" (CC-BY incompetech.com)
# Usage: bash scripts/assemble_demo.sh

set -euo pipefail

SRC="astronomus-demo.mp4"
MUSIC="/tmp/music_test.mp3"
OUT="astronomus-demo-base.mp4"   # combined with features+outtake by build_final.sh
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ── Dead-time sections to 4× speed ──────────────────────────────────────────
# Segment A  0–1s    : normal  (first frame, just starting)
# Segment B  1–6s    : 4× speed (Tonight loading, no forecast yet)
# Segment C  6–7s    : normal  (brief pause, weather strip visible)
# Segment D  7–13s   : 4× speed (catalog "Loading catalog data...")
# Segment E  13–71s  : normal  (all good content)
#
# After 4× speedup:
#   B: 5s → 1.25s
#   D: 6s → 1.5s
#   Total saved: ~8.25s → final raw ≈ 62.75s + 3s title = ~66s

echo "Step 1/5: Splitting into segments..."

# A: 0–1s normal
ffmpeg -y -ss 0 -t 1 -i "$SRC" -c:v libx264 -crf 18 -preset fast /tmp/seg_a.mp4 2>/dev/null

# B: 1–6s → 4× speed
ffmpeg -y -ss 1 -t 5 -i "$SRC" \
  -filter:v "setpts=PTS/4" \
  -c:v libx264 -crf 18 -preset fast /tmp/seg_b.mp4 2>/dev/null

# C: 6–11s normal (5s of homepage so viewers can orient — conditions, 7-day strip, hover)
ffmpeg -y -ss 6 -t 5 -i "$SRC" -c:v libx264 -crf 18 -preset fast /tmp/seg_c.mp4 2>/dev/null

# D: 11–17s → 4× speed (navigation + catalog loading)
ffmpeg -y -ss 11 -t 6 -i "$SRC" \
  -filter:v "setpts=PTS/4" \
  -c:v libx264 -crf 18 -preset fast /tmp/seg_d.mp4 2>/dev/null

# E: 17s+ normal (all good content)
ffmpeg -y -ss 17 -i "$SRC" -c:v libx264 -crf 18 -preset fast /tmp/seg_e.mp4 2>/dev/null

echo "Step 2/5: Making title card (3s)..."
ffmpeg -y -f lavfi \
  -i "color=c=0x0a0a14:size=1440x900:rate=25:duration=3" \
  -vf "drawtext=fontfile='$FONT':text='Astronomus':fontcolor=white:fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2-40:alpha='if(lt(t,0.5),t/0.5,if(lt(t,2.5),1,1-(t-2.5)/0.5))',
       drawtext=fontfile='$FONT':text='Plan your night. Point your scope.':fontcolor=0x9ca3af:fontsize=28:x=(w-text_w)/2:y=(h-text_h)/2+52:alpha='if(lt(t,0.8),0,if(lt(t,1.3),(t-0.8)/0.5,if(lt(t,2.5),1,1-(t-2.5)/0.5)))'" \
  -c:v libx264 -crf 18 -preset fast /tmp/seg_title.mp4 2>/dev/null

echo "Step 3/5: Concatenating segments..."
cat > /tmp/concat_list.txt << 'CONCAT'
file '/tmp/seg_title.mp4'
file '/tmp/seg_a.mp4'
file '/tmp/seg_b.mp4'
file '/tmp/seg_c.mp4'
file '/tmp/seg_d.mp4'
file '/tmp/seg_e.mp4'
CONCAT

ffmpeg -y -f concat -safe 0 -i /tmp/concat_list.txt \
  -c:v libx264 -crf 18 -preset fast /tmp/raw_concat.mp4 2>/dev/null

echo "Step 4/5: Adding captions + fade in/out..."

# Caption timestamps (seconds, accounting for 3s title card + speed-ups):
#   0–3s    : title card
#   3–4s    : seg_a (0–1s original)
#   4–5.25s : seg_b (1–6s original, 4× speed)
#   5.25–10.25s: seg_c (6–11s original, 5s of homepage)
#   10.25–11.75s: seg_d (11–17s original, 4× speed)
#   11.75s+ : seg_e (17s+ original)
# seg_e content mapping (prefix=11.75, E_start=17 → offset = 11.75-17 = -5.25):
#   output_t = original_t - 5.25
#   (recording has +2.5s homepage vs old; events in recording shifted by +2.5s)
#   Original 19.5s → output 14.25s : Deep Sky catalog loaded
#   Original 25s   → output 19.75s : Solar System tab
#   Original 32s   → output 26.75s : Satellites tab (ISS passes)
#   Original 40s   → output 34.75s : Plan view / Generate click
#   Original 45s   → output 39.75s : Scheduled Targets appear
#   Original 48s   → output 42.75s : Timeline hover
#   Original 52s   → output 46.75s : Scrolling target cards (9 × 1.4s = 12.6s)
#   Original 65s   → output 59.75s : Near misses (≤2s)
#   Original 67s   → output 61.75s : Save / Send to Scope

TOTAL_DUR=$(ffprobe -v quiet -show_entries format=duration \
  -of csv=p=0 /tmp/raw_concat.mp4)
echo "  Total duration: ${TOTAL_DUR}s"

ffmpeg -y -i /tmp/raw_concat.mp4 -vf "
  fade=t=in:st=0:d=1,
  fade=t=out:st=$(echo "$TOTAL_DUR - 1.5" | bc):d=1.5,

  drawtext=fontfile='$FONT':
    text='Tonight — conditions \\& 7-day forecast':
    fontcolor=white:fontsize=22:
    x=30:y=h-70:
    box=1:boxcolor=black@0.55:boxborderw=8:
    enable='between(t,3.5,10)',

  drawtext=fontfile='$FONT':
    text='12\\,394 deep-sky objects — scored for your sky':
    fontcolor=white:fontsize=22:
    x=30:y=h-70:
    box=1:boxcolor=black@0.55:boxborderw=8:
    enable='between(t,11.5,14)',

  drawtext=fontfile='$FONT':
    text='Solar System — planets \\& moons with tonight visibility':
    fontcolor=white:fontsize=22:
    x=30:y=h-70:
    box=1:boxcolor=black@0.55:boxborderw=8:
    enable='between(t,14,19)',

  drawtext=fontfile='$FONT':
    text='Satellites — ISS passes for your location':
    fontcolor=white:fontsize=22:
    x=30:y=h-70:
    box=1:boxcolor=black@0.55:boxborderw=8:
    enable='between(t,20,26)',

  drawtext=fontfile='$FONT':
    text='One click — optimized schedule for the whole night':
    fontcolor=white:fontsize=22:
    x=30:y=h-70:
    box=1:boxcolor=black@0.55:boxborderw=8:
    enable='between(t,27,33)',

  drawtext=fontfile='$FONT':
    text='Interactive timeline — drag to reorder':
    fontcolor=white:fontsize=22:
    x=30:y=h-70:
    box=1:boxcolor=black@0.55:boxborderw=8:
    enable='between(t,33,37)',

  drawtext=fontfile='$FONT':
    text='Near misses — high-scoring targets that did not fit':
    fontcolor=white:fontsize=22:
    x=30:y=h-70:
    box=1:boxcolor=black@0.55:boxborderw=8:
    enable='between(t,44,47)',

  drawtext=fontfile='$FONT':
    text='Save and send directly to the Seestar S50':
    fontcolor=white:fontsize=22:
    x=30:y=h-70:
    box=1:boxcolor=black@0.55:boxborderw=8:
    enable='between(t,47,52)',

  drawtext=fontfile='$FONT':
    text='github.com/irjudson/astronomus  ·  CC-BY music: Kevin MacLeod':
    fontcolor=0x6b7280:fontsize=14:
    x=(w-text_w)/2:y=h-28:
    enable='between(t,$(echo "$TOTAL_DUR - 4" | bc),$TOTAL_DUR)'
" \
  -c:v libx264 -crf 17 -preset slow \
  /tmp/captioned.mp4 2>/dev/null

echo "Step 5/5: Mixing in music + final encode..."
ffmpeg -y \
  -i /tmp/captioned.mp4 \
  -i "$MUSIC" \
  -filter_complex "
    [1:a]volume=0.10,afade=t=in:st=0:d=2,afade=t=out:st=$(echo "$TOTAL_DUR - 3" | bc):d=3[music];
    [music]apad[aout]
  " \
  -map 0:v -map "[aout]" \
  -c:v libx264 -crf 17 -preset slow \
  -c:a aac -b:a 192k \
  -movflags +faststart \
  -shortest \
  "$OUT"

echo ""
echo "Done! → $OUT"
echo "Next: node scripts/record_features.js && bash scripts/assemble_features.sh && bash scripts/build_final.sh"
ffprobe -v quiet -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUT"
