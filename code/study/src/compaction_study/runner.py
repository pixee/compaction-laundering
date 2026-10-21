"""Incremental, observable, resumable cell execution.

Written after a GLM run sat at 2h46m with zero visibility and had to be killed, losing every
completed cell. Three properties every long run needs and the first version had none of:

1. **Incremental writes** — each result is appended the moment it lands, so a killed run keeps
   everything it finished.
2. **Progress** — completion count, rate, and ETA on stderr, so "is it stuck or just slow?" is
   answerable without guessing.
3. **Resume** — re-running the same command skips cells already present in the output file.

The trigger for all three is per-family concurrency: pinning a rate-limited vendor to 1 is
correct, and it is exactly the setting that makes a run long enough to need observability.
"""

from __future__ import annotations

import asyncio
import json
import math
import sys
import time
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path

CellKey = tuple[str, ...]
"""Identity of one cell — must be stable across runs for resume to work."""


def _load_rows(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # a torn final line from a hard kill; ignore it
    return rows


def _load_done(rows: Sequence[dict[str, object]], key_fields: Sequence[str]) -> set[CellKey]:
    """Keys of cells that **succeeded**.

    Errored rows are deliberately NOT counted as done. Treating them as complete would make a
    resume pass skip precisely the cells it exists to retry — turning a recoverable rate-limit
    loss into a permanent hole in the grid. On a vendor shedding ~46% of cells per pass, that is
    the difference between "run it twice" and "the data is gone".
    """
    return {
        tuple(str(row.get(f)) for f in key_fields)
        for row in rows
        if not row.get("error")
    }


def _fmt_eta(seconds: float) -> str:
    if seconds < 0 or math.isnan(seconds):
        return "?"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m{s:02d}s"


async def run_cells(
    cells: Sequence[tuple[CellKey, Callable[[], Awaitable[dict[str, object]]]]],
    out_path: str,
    key_fields: Sequence[str],
    *,
    resume: bool = True,
    log_every: int | None = None,
) -> list[dict[str, object]]:
    """Execute cells, appending each result as it completes.

    `cells` pairs a stable key with a thunk producing the row. `key_fields` names the row fields
    that reconstruct that key, so a resumed run can tell what is already done.

    Returns every row for this invocation *plus* any rows recovered from a previous run, so the
    caller's report covers the full grid rather than only the newly-executed slice.
    """
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = _load_rows(path) if resume else []
    done = _load_done(existing, key_fields)
    # Carry forward only the successful rows; failed ones are about to be retried and their
    # stale error records would otherwise be double-counted in the report.
    prior = [r for r in existing if not r.get("error")]
    if existing:
        failed = len(existing) - len(prior)
        note = f", {failed} failed and will be retried" if failed else ""
        print(f"resuming: {len(done)} cells complete{note}", file=sys.stderr)

    todo = [(key, thunk) for key, thunk in cells if key not in done]
    total = len(todo)
    if not todo:
        print("nothing to do — grid already complete", file=sys.stderr)
        return prior

    # ~50 progress lines regardless of grid size: a 45-cell run at 1 cell/min printed nothing
    # for two minutes under a fixed stride, which is the opposite of the point.
    if log_every is None:
        log_every = max(1, total // 50)

    print(f"running {total} cells (of {len(cells)} total)", file=sys.stderr)

    started = time.monotonic()
    completed = 0
    errors = 0
    results: list[dict[str, object]] = []
    lock = asyncio.Lock()

    # Append mode: a resumed run must not truncate what the previous one earned. The handle is
    # opened before the loop and each write is flushed, so a kill -9 keeps completed cells;
    # blocking I/O is fine here because writes are tiny and serialized behind `lock`.
    fh = path.open("a", encoding="utf-8")  # noqa: ASYNC230
    try:

        async def one(thunk: Callable[[], Awaitable[dict[str, object]]]) -> None:
            nonlocal completed, errors
            row = await thunk()
            async with lock:
                completed += 1
                if row.get("error"):
                    errors += 1
                fh.write(json.dumps(row) + "\n")
                fh.flush()  # survive a kill -9, not just a clean exit
                results.append(row)
                if completed % log_every == 0 or completed == total:
                    elapsed = time.monotonic() - started
                    rate = completed / elapsed if elapsed else 0.0
                    eta = (total - completed) / rate if rate else float("nan")
                    print(
                        f"  {completed}/{total}  {rate * 60:.1f}/min  "
                        f"eta {_fmt_eta(eta)}  errors {errors}",
                        file=sys.stderr,
                    )

        await asyncio.gather(*(one(thunk) for _, thunk in todo))
    finally:
        fh.close()

    return prior + results
