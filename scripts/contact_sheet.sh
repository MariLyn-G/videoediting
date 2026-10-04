#!/usr/bin/env bash
# Contact sheet of a video for visual QA: one frame every N seconds, 8 per row.
#   contact_sheet.sh video.mp4 out.jpg [seconds_between_frames=1] [start=0] [end=]
set -euo pipefail
in="$1"; out="$2"; step="${3:-1}"; start="${4:-0}"; end="${5:-}"
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
end="${end:-$dur}"
n=$(python3 -c "import math; print(max(1, math.ceil(($end - $start) / $step)))")
rows=$(( (n + 7) / 8 ))
ffmpeg -hide_banner -v error -y -ss "$start" -to "$end" -i "$in" \
  -vf "fps=1/$step,scale=240:-2,drawtext=text='%{pts\:hms}':x=6:y=6:fontsize=18:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=8x$rows" \
  -frames:v 1 "$out" 2>/dev/null || \
ffmpeg -hide_banner -v error -y -ss "$start" -to "$end" -i "$in" \
  -vf "fps=1/$step,scale=240:-2,tile=8x$rows" -frames:v 1 "$out"
echo "$out ($n frames from ${start}s, every ${step}s)"
