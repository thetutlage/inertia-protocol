#!/usr/bin/env bash
#
# Renders D2 diagram sources (*.d2) to SVG with the spec's green theme and
# JetBrains Mono labels.
#
#   ./render.sh *.d2            # render given files
#   ./render.sh                 # render every *.d2 in this directory
#   FONT_DIR=/path ./render.sh  # use JetBrains Mono TTFs from a specific dir
#
# Requirements:
#   - d2          https://d2lang.com           (brew install d2)
#   - JetBrains Mono TTFs installed            https://www.jetbrains.com/lp/mono/
#
set -euo pipefail

command -v d2 >/dev/null || { echo "error: d2 not found — install from https://d2lang.com"; exit 1; }

DIR="$(cd "$(dirname "$0")" && pwd)"
FONT_DIR="${FONT_DIR:-}"

# Auto-detect a directory containing JetBrains Mono static TTFs.
if [ -z "$FONT_DIR" ]; then
  for d in "$HOME/Library/Fonts" "$HOME/.fonts" "$HOME/.local/share/fonts" \
           "/usr/share/fonts" "/usr/local/share/fonts" "/Library/Fonts"; do
    if ls "$d"/JetBrainsMono*-Regular.ttf >/dev/null 2>&1; then FONT_DIR="$d"; break; fi
  done
fi
[ -n "$FONT_DIR" ] || { echo "error: JetBrains Mono TTFs not found. Install them, or set FONT_DIR=/path/to/ttfs"; exit 1; }

# Resolve a TTF for a given style, preferring the no-ligature (NL) cut.
font() {
  for base in "JetBrainsMonoNL-$1" "JetBrainsMono-$1"; do
    local f="$FONT_DIR/$base.ttf"
    [ -f "$f" ] && { echo "$f"; return; }
  done
  echo "error: JetBrainsMono $1 TTF not found in $FONT_DIR" >&2; exit 1
}

files=("$@")
[ ${#files[@]} -eq 0 ] && files=("$DIR"/*.d2)

for f in "${files[@]}"; do
  d2 --pad 10 \
     --font-regular  "$(font Regular)" \
     --font-italic   "$(font Italic)" \
     --font-bold     "$(font Bold)" \
     --font-semibold "$(font SemiBold)" \
     "$f" "${f%.d2}.svg"
done
