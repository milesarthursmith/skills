#!/usr/bin/env bash
# sbs.sh <left.webm> <right.webm> <out.mp4> "<left label>" "<right label>" [height=540]
# Labels may contain colons (escaped for ffmpeg); apostrophes are dropped.
# Stacks two clips side by side (each scaled to the same height), labels them, pads the shorter one, outputs H.264 MP4.
set -euo pipefail
L="$1"; R="$2"; OUT="$3"; LL="$4"; RL="$5"; HT="${6:-540}"
FONT=$(fc-match -f '%{file}' 'DejaVu Sans:bold' 2>/dev/null || echo /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf)
lab() { local t="${1//:/\\:}"; t="${t//\x27/}"; echo "drawtext=fontfile=$FONT:text='$t':x=14:y=14:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=8"; }
ffmpeg -y -loglevel error -i "$L" -i "$R" -filter_complex \
 "[0:v]scale=-2:$HT,setsar=1,$(lab "$LL"),tpad=stop_mode=clone:stop_duration=30[a];[1:v]scale=-2:$HT,setsar=1,$(lab "$RL"),tpad=stop_mode=clone:stop_duration=30[b];[a][b]hstack=inputs=2:shortest=0,pad=ceil(iw/2)*2:ceil(ih/2)*2,trim=duration=$(python3 -c "import subprocess as s;d=lambda f:float(s.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]));print(max(d('$L'),d('$R')))")" \
 -c:v libx264 -crf 26 -preset veryfast -pix_fmt yuv420p -movflags +faststart -an "$OUT"
echo "side-by-side → $OUT"
