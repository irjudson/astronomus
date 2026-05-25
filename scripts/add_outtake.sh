#!/usr/bin/env bash
# Appends an "outtake" features card to the assembled demo video.
set -euo pipefail

IN="astronomus-demo-final.mp4"
OUT="astronomus-demo-final.mp4"   # overwrite in place
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
DURATION=14   # seconds for the outtake card

# Features appear one by one, 1.4s apart starting at t=2
# Layout:
#   t=0.5  header fades in
#   t=2.0  Live Observing
#   t=3.4  Post-Processing
#   t=4.8  Horizon Scanner
#   t=6.2  Custom Targets
#   t=7.6  Local Weather Station
#   t=9.0  Satellite Avoidance
#   t=10.4 Polar Alignment
#   t=12   footer fades in

echo "Building outtake card (${DURATION}s)..."
ffmpeg -y -f lavfi \
  -i "color=c=0x080810:size=1440x900:rate=25:duration=${DURATION}" \
  -vf "
    fade=t=in:st=0:d=0.5,
    fade=t=out:st=$((DURATION-1)):d=1,

    drawtext=fontfile='$FONT':
      text='Also in the app — not shown here':
      fontcolor=white:fontsize=40:
      x=(w-text_w)/2:y=110:
      alpha='if(lt(t,0.5),0,if(lt(t,1),(t-0.5)/0.5,1))',

    drawtext=fontfile='$FONT_REG':
      text='▶  Live Observing — real-time control\, target tracking\, skip \& extend':
      fontcolor=0x60a5fa:fontsize=26:x=180:y=230:
      alpha='if(lt(t,2.0),0,if(lt(t,2.4),(t-2.0)/0.4,1))',

    drawtext=fontfile='$FONT_REG':
      text='▶  Horizon Scanner — telescope sweeps to map your terrain boundary':
      fontcolor=0xfbbf24:fontsize=26:x=180:y=290:
      alpha='if(lt(t,3.4),0,if(lt(t,3.8),(t-3.4)/0.4,1))',

    drawtext=fontfile='$FONT_REG':
      text='▶  Satellite Avoidance — Celestrak TLE integration blocks passes':
      fontcolor=0xf87171:fontsize=26:x=180:y=350:
      alpha='if(lt(t,4.8),0,if(lt(t,5.2),(t-4.8)/0.4,1))',

    drawtext=fontfile='$FONT_REG':
      text='▶  Local Weather Station — live seeing data from your own sensor':
      fontcolor=0x38bdf8:fontsize=26:x=180:y=410:
      alpha='if(lt(t,6.2),0,if(lt(t,6.6),(t-6.2)/0.4,1))',

    drawtext=fontfile='$FONT_REG':
      text='▶  Custom Targets — add any object with your own RA\\/Dec':
      fontcolor=0xa78bfa:fontsize=26:x=180:y=470:
      alpha='if(lt(t,7.6),0,if(lt(t,8.0),(t-7.6)/0.4,1))',

    drawtext=fontfile='$FONT_REG':
      text='▶  Polar Alignment — assisted alignment using drift analysis':
      fontcolor=0xfb923c:fontsize=26:x=180:y=530:
      alpha='if(lt(t,9.0),0,if(lt(t,9.4),(t-9.0)/0.4,1))',

    drawtext=fontfile='$FONT':
      text='Post-processing pipeline — coming next':
      fontcolor=0x6b7280:fontsize=24:
      x=(w-text_w)/2:y=650:
      alpha='if(lt(t,10.4),0,if(lt(t,10.8),(t-10.4)/0.4,1))',

    drawtext=fontfile='$FONT_REG':
      text='github.com/irjudson/astronomus':
      fontcolor=0x4b5563:fontsize=20:
      x=(w-text_w)/2:y=800:
      alpha='if(lt(t,12),0,if(lt(t,12.5),(t-12)/0.5,1))'
  " \
  -c:v libx264 -crf 17 -preset slow \
  /tmp/outtake.mp4 2>/dev/null

echo "Concatenating to final video..."
# Re-add music continuation over the outtake
MUSIC="/tmp/music_test.mp3"
MAIN_DUR=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$IN")

# Get music offset (so we continue where the main video left off)
cat > /tmp/concat2.txt << CONCAT
file '$(realpath "$IN")'
file '/tmp/outtake.mp4'
CONCAT

ffmpeg -y -f concat -safe 0 -i /tmp/concat2.txt \
  -i "$MUSIC" \
  -filter_complex "
    [1:a]volume=0.10,
      adelay=${MAIN_DUR}000|${MAIN_DUR}000,
      afade=t=in:st=${MAIN_DUR}:d=1,
      afade=t=out:st=$(echo "$MAIN_DUR + $DURATION - 2" | bc):d=2[outtake_music];
    [0:a][outtake_music]amix=inputs=2:duration=first[aout]
  " \
  -map 0:v -map "[aout]" \
  -c:v libx264 -crf 17 -preset slow \
  -c:a aac -b:a 192k \
  -movflags +faststart \
  /tmp/with_outtake.mp4 2>/dev/null

mv /tmp/with_outtake.mp4 "$OUT"

echo ""
echo "Done! → $OUT"
ffprobe -v quiet -show_entries format=duration,size -of default=noprint_wrappers=1 "$OUT"
