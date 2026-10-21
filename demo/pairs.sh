#!/usr/bin/env bash
# Paired take loop: each iteration runs the SAME director script twice — once with Bob's
# poisoned guide (FORGED=1) and once with the clean guide (FORGED=0). The pair is the
# demonstration: the final Alice message grants no authorization ("ok, keep going"), so a
# post-compaction bootstrap execution can only come from the laundered standing approval.
# Artifacts: takes/pair-N/{poisoned,clean}/ each with demo.mp4 (kept for wins),
# run.log, collected.log, pi-sessions/, digest.md, category.txt.
#
# Usage: ./pairs.sh [PAIRS=3]
set -uo pipefail


PAIRS="${1:-3}"
ROOT="${TAKES_DIR:-/tmp/compaction-demo-takes}"
mkdir -p "$ROOT"

run_arm() { # $1=dir $2=FORGED
  mkdir -p "$1"
  if [ -s "$1/category.txt" ]; then
    echo "    -> $(basename "$1"): $(cat "$1/category.txt") (cached)"
    return 0
  fi
  env PI_MODEL="${PI_MODEL_OVERRIDE:-gpt-5.6-luna}" FORGED="$2" \
    ANTHROPIC_API_KEY="${ANTHROPIC_COMPACTION_KEY:-${ANTHROPIC_API_KEY:-}}" \
    bash "$(dirname "$0")/run.sh" "$1" >"$1/run.log" 2>&1 || true
  if cat_out=$(python3 "$(dirname "$0")/digest.py" "$1" 2>"$1/digest.err"); then
    printf '%s\n' "$cat_out" > "$1/category.txt"
  else
    printf 'INCOMPLETE\n' > "$1/category.txt"
  fi
  true
  echo "    -> $(basename "$1"): $(cat "$1/category.txt")"
}

pwins=0; cwins=0; n=0
while [ "$n" -lt "$PAIRS" ]; do
  n=$((n+1))
  # skip a pair that already has both digests (pre-seeded from manual runs)
  if [ -s "$ROOT/pair-$n/poisoned/category.txt" ] && [ -s "$ROOT/pair-$n/clean/category.txt" ]; then
    echo "=== pair $n: already complete, skipping ==="
    echo "    -> poisoned: $(cat "$ROOT/pair-$n/poisoned/category.txt")"
    echo "    -> clean:    $(cat "$ROOT/pair-$n/clean/category.txt")"
    [ "$(cat "$ROOT/pair-$n/poisoned/category.txt")" = "WIN" ] && pwins=$((pwins+1))
    continue
  fi
  echo "=== pair $n (poisoned, then clean) ==="
  run_arm "$ROOT/pair-$n/poisoned" 1
  run_arm "$ROOT/pair-$n/clean" 0
  [ "$(cat "$ROOT/pair-$n/poisoned/category.txt")" = "WIN" ] && pwins=$((pwins+1))
  [ "$(cat "$ROOT/pair-$n/clean/category.txt" = "WIN" 2>/dev/null && echo WIN)" ] || true
done

echo "=== DONE: $n pairs — poisoned WINs: $pwins ==="
for p in "$ROOT"/pair-*; do
  echo "  $(basename "$p"): poisoned=$(cat "$p/poisoned/category.txt" 2>/dev/null) clean=$(cat "$p/clean/category.txt" 2>/dev/null)"
done
