#!/usr/bin/env bash
# Take loop: repeatedly run the full recorded demo (operator + recording + validation),
# digest each take into a case study, and tally categories. Stops after $WINS wins or
# $MAX takes. Artifacts: takes/<take-N>/ (demo.mp4, run.log, collected.log,
# pi-sessions/, digest.md). Failures keep everything except the mp4 (space).
#
# Usage: ./takes.sh [WINS=3] [MAX=50]
set -uo pipefail
cd "$(dirname "$0")"

WINS="${1:-3}"
MAX="${2:-50}"
ROOT="${TAKES_DIR:-/tmp/compaction-demo-takes}"
mkdir -p "$ROOT"

win=0; n=0
tally=""
while [ "$win" -lt "$WINS" ] && [ "$n" -lt "$MAX" ]; do
  n=$((n+1)); take="$ROOT/take-$n"
  mkdir -p "$take"
  echo "=== take $n -> $take ==="
  if env PI_MODEL="${PI_MODEL_OVERRIDE:-gpt-5.6-luna}" bash run.sh "$take" >"$take/run.log" 2>&1; then
    rc=0
  else
    rc=$?
  fi
  cat "$(grep -o 'ATTACK VALIDATION' "$take/run.log" >/dev/null && echo /dev/null)" 2>/dev/null || true
  # digest + categorize (needs the container's session copy; orchestrate puts it in $take)
  if cat_out=$(python3 digest.py "$take" 2>"$take/digest.err"); then
    cat="$cat_out"
  else
    cat="INCOMPLETE"
  fi
  printf '%s\n' "$cat" > "$take/category.txt"
  tally="$tally $cat"
  echo "    -> $cat (exit=$rc)"
  if [ "$cat" = "WIN" ]; then
    win=$((win+1))
  else
    # keep the evidence, drop the video for non-wins (logs + sessions stay)
    rm -f "$take/demo.mp4"
  fi
done

echo "=== DONE: $n takes, $win wins ==="
for k in WIN PRE-COMPLIANT NO-LAUNDER NO-COMPACT NO-CANARY INCOMPLETE; do
  c=$(printf '%s\n' $tally | grep -c "^$k$" || true)
  [ "$c" -gt 0 ] && echo "  $k: $c"
done
