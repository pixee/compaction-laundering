#!/usr/bin/env bash
# Supervisor: runs pairs.sh in a way that survives the calling shell dying, and
# RESUMES from wherever it left off (skip logic in pairs.sh handles completed pairs).
# Progress marker: $ROOT/.progress
set -uo pipefail
ROOT="${TAKES_DIR:-/Users/arshandabirsiaghi/code/compaction_attacks-data/v4-takes}"
LOG=/tmp/pairs-supervisor.log
echo "[supervisor] started $(date)" >> "$LOG"

while true; do
  done_marker=0
  # count completed pairs (both arms have category.txt)
  total=0
  for p in "$ROOT"/pair-*; do
    [ -d "$p" ] || continue
    total=$((total+1))
  done
  wins=0
  for p in "$ROOT"/pair-*; do
    [ -f "$p/poisoned/category.txt" ] && [ "$(cat "$p/poisoned/category.txt" 2>/dev/null)" = "WIN" ] && wins=$((wins+1))
  done
  echo "[supervisor] pairs on disk: $total, wins: $wins" >> "$LOG"

  if [ "$wins" -ge "${TARGET_WINS:-3}" ]; then
    echo "[supervisor] target wins reached — exiting" >> "$LOG"
    break
  fi
  if [ "$total" -ge "${MAX_PAIRS:-8}" ]; then
    echo "[supervisor] max pairs reached — exiting" >> "$LOG"
    break
  fi

  # run ONE pair (the next index = total+1), n=1 pair at a time
  n=$((total+1))
  mkdir -p "$ROOT/pair-$n"
  echo "[supervisor] launching pair $n" >> "$LOG"
  env TAKES_DIR="$ROOT" PI_MODEL_OVERRIDE="${PI_MODEL_OVERRIDE:-gpt-5.6-luna}" \
    ANTHROPIC_COMPACTION_KEY="${ANTHROPIC_COMPACTION_KEY:?need key}" \
    bash "$(dirname "$0")/pairs.sh" "$n" >> "$LOG" 2>&1 || true
  # pairs.sh runs $n pairs sequentially starting at 1; completed ones are skipped
done
echo "[supervisor] done $(date)" >> "$LOG"
