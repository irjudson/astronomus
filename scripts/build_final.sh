#!/usr/bin/env bash
# Final assembly: main demo + feature highlights + outtake card → final video
# Music: Kevin MacLeod — "Slow Burn" (CC-BY incompetech.com)
#
# Inputs:  astronomus-demo-base.mp4   (from assemble_demo.sh)
#          astronomus-features.mp4    (from assemble_features.sh)
# Output:  astronomus-demo-final.mp4
#
# Full pipeline:
#   1. node scripts/record_demo.js
#   2. bash scripts/assemble_demo.sh
#   3. node scripts/record_features.js
#   4. bash scripts/assemble_features.sh
#   5. bash scripts/build_final.sh   ← this script
set -euo pipefail

BASE="astronomus-demo-base.mp4"
MUSIC="/tmp/music_test.mp3"
OUT="astronomus-demo-final.mp4"
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
OUTTAKE_DUR=12   # seconds for the outtake card (4 features + footer)

for f in "$BASE" "$MUSIC"; do
  if [[ ! -f "$f" ]]; then
    echo "ERROR: $f not found."
    exit 1
  fi
done

# ── Step 1: Create outtake card ───────────────────────────────────────────────
# Shows features in the app that aren't demoed in the main video.
# Features appear 1.4s apart with 0.4s fade.
# Layout:
#   t=0.5  header fades in
#   t=2.0  Live Observing
#   t=3.4  Horizon Scanner
#   t=4.8  Custom Targets
#   t=6.2  Polar Alignment
#   t=7.6  footer fades in
echo "Step 1/4: Building outtake card (${OUTTAKE_DUR}s)..."
ffmpeg -y -f lavfi \
  -i "color=c=0x080810:size=1440x900:rate=25:duration=${OUTTAKE_DUR}" \
  -vf "
    fade=t=in:st=0:d=0.5,
    fade=t=out:st=$((OUTTAKE_DUR-1)):d=1,

    drawtext=fontfile='$FONT':
      text='Also in the app — not shown here':
      fontcolor=white:fontsize=40:
      x=(w-text_w)/2:y=150:
      alpha='if(lt(t,0.5),0,if(lt(t,1),(t-0.5)/0.5,1))',

    drawtext=fontfile='$FONT_REG':
      text='▶  Live Observing — stay in control\, adapt and extend your session in real time':
      fontcolor=0x60a5fa:fontsize=26:x=180:y=280:
      alpha='if(lt(t,2.0),0,if(lt(t,2.4),(t-2.0)/0.4,1))',

    drawtext=fontfile='$FONT_REG':
      text='▶  Horizon Scanner — scan the horizon to maximize observable sky':
      fontcolor=0xfbbf24:fontsize=26:x=180:y=340:
      alpha='if(lt(t,3.4),0,if(lt(t,3.8),(t-3.4)/0.4,1))',

    drawtext=fontfile='$FONT_REG':
      text='▶  Custom Targets — image anything in the sky\, beyond the built-in catalog':
      fontcolor=0xa78bfa:fontsize=26:x=180:y=400:
      alpha='if(lt(t,4.8),0,if(lt(t,5.2),(t-4.8)/0.4,1))',

    drawtext=fontfile='$FONT_REG':
      text='▶  Polar Alignment — unlock equatorial mode for sharper\, longer exposures':
      fontcolor=0xfb923c:fontsize=26:x=180:y=460:
      alpha='if(lt(t,6.2),0,if(lt(t,6.6),(t-6.2)/0.4,1))',

    drawtext=fontfile='$FONT':
      text='Post-processing pipeline coming soon...':
      fontcolor=0x6b7280:fontsize=24:
      x=(w-text_w)/2:y=575:
      alpha='if(lt(t,7.6),0,if(lt(t,8.0),(t-7.6)/0.4,1))',

    drawtext=fontfile='$FONT_REG':
      text='(Manage your astrophotography images in Lumina!)':
      fontcolor=0x4b5563:fontsize=20:
      x=(w-text_w)/2:y=612:
      alpha='if(lt(t,7.6),0,if(lt(t,8.0),(t-7.6)/0.4,1))',

    drawtext=fontfile='$FONT_REG':
      text='github.com/irjudson/astronomus':
      fontcolor=0x4b5563:fontsize=20:
      x=(w-text_w)/2:y=800:
      alpha='if(lt(t,9),0,if(lt(t,9.5),(t-9)/0.5,1))'
  " \
  -c:v libx264 -crf 17 -preset slow \
  /tmp/outtake.mp4 2>/dev/null

# ── Step 2: Concatenate video tracks ─────────────────────────────────────────
echo "Step 2/4: Concatenating base + outtake..."
BASE_DUR=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$BASE")
TOTAL_VIDEO_DUR=$(echo "$BASE_DUR + $OUTTAKE_DUR" | bc)
echo "  Base: ${BASE_DUR}s  Outtake: ${OUTTAKE_DUR}s  Total: ${TOTAL_VIDEO_DUR}s"

cat > /tmp/final_concat.txt << CONCAT
file '$(realpath "$BASE")'
file '/tmp/outtake.mp4'
CONCAT

ffmpeg -y -f concat -safe 0 -i /tmp/final_concat.txt \
  -c:v libx264 -crf 17 -preset slow \
  /tmp/final_noaudio.mp4 2>/dev/null

# ── Step 3: Mix in music ──────────────────────────────────────────────────────
# Music fades in at start of video, fades out near end.
# Volume kept low (0.10) so narration/UI sounds aren't masked.
echo "Step 3/4: Mixing music..."
FADE_OUT_START=$(echo "$TOTAL_VIDEO_DUR - 3" | bc)
ffmpeg -y \
  -i /tmp/final_noaudio.mp4 \
  -i "$MUSIC" \
  -filter_complex "
    [1:a]volume=0.10,afade=t=in:st=0:d=2,afade=t=out:st=${FADE_OUT_START}:d=3[music];
    [music]apad[aout]
  " \
  -map 0:v -map "[aout]" \
  -c:v copy \
  -c:a aac -b:a 192k \
  -movflags +faststart \
  -shortest \
  /tmp/final_mixed.mp4 2>/dev/null

# ── Step 4: Final encode ──────────────────────────────────────────────────────
echo "Step 4/4: Final encode..."
mv /tmp/final_mixed.mp4 "$OUT"

echo ""
echo "Done! → $OUT"
ffprobe -v quiet -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUT"
