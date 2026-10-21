"""Extend the laundering-vs-size sweep toward a ~1M-token window (pi).

run_context_scale established that pi's forged-approval laundering is flat at ~100% out to ~307k
tokens (260 units). This closes the top of the curve: the same buried `[User]:` approval, the same
real pi compaction prompt, pushed up toward a million-token window — the largest a real session
would ever compact. Tiers that exceed the model's context limit are caught and recorded, not hidden.

pi only (the flattening harness under test), model = gpt-5.6-terra, poison ~75% deep. Reuses
run_context_scale's transcript builder, poison, and scorer verbatim; only the size tiers change.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import run_context_scale as C  # noqa: E402
from compaction_study.types import HarnessName  # noqa: E402

# ~1180 summarizer tokens/unit (measured). terra's hard input ceiling is 922k tokens: 850u (~1.0M)
# and 1000u (~1.18M) are rejected, so the top of the real window is probed at 740u (~873k) and
# 770u (~908k), just under the cap. 430/620/850/1000 are already recorded and merged from disk.
TIERS = (740, 770)
REPS = 3


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)
    out_path = Path(__file__).resolve().parent / "context_scale_1m_result.json"
    grid: dict = json.loads(out_path.read_text()) if out_path.exists() else {}
    print(f"model={C.MODEL}  reps={REPS}  tiers(units)={TIERS}  harness=pi\n", flush=True)
    for units in TIERS:
        key = f"pi @ {units}u"
        cells = []
        for rep in range(REPS):
            cell = C.run_one(units, HarnessName.PI, rep)
            cells.append(cell.__dict__ | {"harness": "pi"})
            grid[key] = cells
            out_path.write_text(json.dumps(grid, indent=2))
            tag = f"ERR {cell.error}" if cell.error else \
                f"tok={cell.prompt_tokens:>8} flipped={cell.flipped} mentioned={cell.mentioned}"
            print(f"  {key:<14} rep {rep + 1}/{REPS}: {tag}", flush=True)
        print(flush=True)

    print("=" * 70)
    print(f"LAUNDERING vs CONTEXT SIZE — 1M extension (pi, {C.MODEL}, n={REPS})")
    print("=" * 70)
    print(f"{'units':<10}{'~tokens':>12}{'flipped':>12}")
    print("-" * 70)
    for key, cells in grid.items():
        ok = [c for c in cells if not c["error"]]
        if not ok:
            print(f"{key:<10}{'—':>12}{'(all over context limit)':>28}")
            continue
        med = sorted(c["prompt_tokens"] for c in ok)[len(ok) // 2]
        rate = f"{sum(c['flipped'] for c in ok)}/{len(ok)}"
        over = len(cells) - len(ok)
        note = f"  ({over} over-limit)" if over else ""
        print(f"{key:<10}{med:>12}{rate:>12}{note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
