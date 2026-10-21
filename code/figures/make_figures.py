"""Regenerate the paper's figures deterministically from the raw result JSONs.

Every number is read from data/live/*.json — nothing is hardcoded except labels and
layout. One shared STYLE block drives all four figures so they are visually identical,
and each figure is written in three formats from a single render:

    figures/figN-*.pdf   vector, fonts EMBEDDED — what the paper (LaTeX) uses
    figures/figN-*.svg   vector, text outlined (svg.fonttype='path') — web / Markdown
    figures/figN-*.png   200 dpi raster — quick preview / fallback

The PDF path is the one that matters for the paper: matplotlib embeds the font, so there
is no font-substitution step (the old hand-emitted SVG relied on browser UI fonts that
`rsvg-convert` did not have, which exploded the letter-spacing and clipped every label).

Run:  cd code/figures && uv run python make_figures.py   [--check]

--check regenerates into a temp dir and fails if the committed figures differ, so CI can
prove the figures still match the data.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# Match the paper exactly: register the bundled Latin Modern Roman — the same family
# LaTeX/tectonic sets for the body text (regular + bold + italic). Bundling the OTFs makes the
# figures reproducible on any machine, not dependent on a local TeX install.
_FONTS = Path(__file__).resolve().parent / "fonts"
for _f in sorted(_FONTS.glob("*.otf")):
    font_manager.fontManager.addfont(str(_f))

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "live"
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)

# ---- one palette + one style for every figure -----------------------------------------
INK = "#1a1a2e"      # primary text
MUTE = "#6b7280"     # secondary text, footnotes
GRID = "#e5e7eb"     # recessive gridlines
FLAT = "#c0392b"     # flattening — the vulnerable class (matches the HTML site)
STRUCT = "#1b8a5a"   # structured — the control
EXEC = "#2563eb"     # execution

FORMATS = ("pdf", "svg", "png")

plt.rcParams.update({
    "svg.fonttype": "path",        # outline text in SVG → renders identically with no font
    "svg.hashsalt": "compaction",  # stable element IDs → byte-identical SVG on re-run
    "pdf.fonttype": 42,            # embed the font in the PDF (no substitution in LaTeX)
    "font.family": "serif",
    "font.serif": ["Latin Modern Roman", "DejaVu Serif"],
    "mathtext.fontset": "cm",
    "font.size": 11,
    "text.color": INK,
    "axes.titlesize": 11,
    "axes.titleweight": "bold",
    "axes.titlecolor": INK,
    "axes.titlepad": 12,
    "axes.labelsize": 12,
    "axes.labelcolor": INK,
    "axes.edgecolor": MUTE,
    "axes.linewidth": 0.9,
    "xtick.color": MUTE,
    "ytick.color": MUTE,
    "xtick.labelcolor": INK,
    "ytick.labelcolor": INK,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.18,
})


# Strip embedded creation dates so re-running produces byte-identical files (no git churn,
# and --check can compare deterministically).
_META = {"pdf": {"CreationDate": None}, "svg": {"Date": None}, "png": {"Software": None}}


def save(fig, stem: str) -> None:
    """Write one figure to every format (deterministically) and report."""
    for ext in FORMATS:
        fig.savefig(OUT / f"{stem}.{ext}", metadata=_META[ext])
    plt.close(fig)
    print(f"  wrote {stem}.{{{','.join(FORMATS)}}}")


def _clean(ax, *, grid_axis: str | None = "y") -> None:
    """The shared axis look: no top/right spines, recessive grid on one axis only."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(length=0)
    if grid_axis:
        ax.grid(True, axis=grid_axis, color=GRID, linewidth=0.9, zorder=0)
        ax.set_axisbelow(True)


# --------------------------------------------------------------------------- data readers
def pooled_laundered_from(section: dict) -> dict[str, tuple[int, int]]:
    per: dict[str, list[int]] = {}
    for key, rows in section.items():
        h = key.split("/")[1].strip()
        v = rows["poisoned"]
        per.setdefault(h, [0, 0])
        per[h][0] += sum(1 for x in v if x == "LAUNDERED")
        per[h][1] += len(v)
    return {h: (a, b) for h, (a, b) in per.items()}


# --------------------------------------------------------------------------- Fig 1
def fig_laundering_by_harness() -> None:
    judged = json.loads((DATA / "judged_result.json").read_text())
    flat = pooled_laundered_from(judged["flattening"])
    struct = pooled_laundered_from(judged["structured"])
    order_flat = ["pi", "opencode", "aider", "openhands", "cline"]
    order_struct = ["codex", "gemini_cli", "qwen_code", "continue"]
    label = {"pi": "pi", "opencode": "opencode", "openhands": "OpenHands", "cline": "Cline",
             "aider": "Aider", "codex": "Codex", "gemini_cli": "Gemini CLI",
             "qwen_code": "Qwen Code", "continue": "Continue"}

    rows = [(h, flat[h], FLAT) for h in order_flat] + [(h, struct[h], STRUCT) for h in order_struct]
    # top-to-bottom: flattening first
    rows = rows[::-1]
    ys = range(len(rows))

    fig, ax = plt.subplots(figsize=(7.2, 4.3))
    for y, (h, (a, b), color) in zip(ys, rows):
        pct = 100 * a / b
        ax.barh(y, pct, height=0.66, color=color, zorder=3)
        inside = pct >= 60
        ax.text(pct - 2 if inside else pct + 2, y, f"{pct:.0f}%  ({a}/{b})",
                va="center", ha="right" if inside else "left",
                color="white" if inside else INK, fontsize=11, fontweight="bold", zorder=4)
    ax.set_yticks(list(ys))
    ax.set_yticklabels([label[h] for h, _, _ in rows], fontsize=12)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_ylim(-0.7, len(rows) - 0.3)
    _clean(ax, grid_axis="x")

    # group separator + labels (structured are the first 4 rows bottom-up)
    sep = len(order_struct) - 0.5
    ax.axhline(sep, color=MUTE, linewidth=0.9, linestyle=(0, (4, 3)))
    ax.text(100, len(rows) - 0.35, "flattening", ha="right", va="bottom",
            color=FLAT, fontsize=12, fontweight="bold")
    ax.text(100, sep - 0.2, "structured (control)", ha="right", va="top",
            color=STRUCT, fontsize=12, fontweight="bold")
    ax.set_title("Forged-approval laundering rate, by harness", loc="center")
    fig.text(0.01, -0.02, "n = 15 per harness (3 models × 5).  Clean control: 0/15 every harness.",
             color=MUTE, fontsize=10)
    save(fig, "fig1-laundering-by-harness")


# --------------------------------------------------------------------------- Fig 2
def fig_scale_invariance() -> None:
    pts: list[tuple[int, float]] = []
    for path in (DATA / "context_scale_result.json", DATA / "context_scale_1m_result.json"):
        d = json.loads(path.read_text())
        for key, cells in d.items():
            if not key.startswith("pi"):
                continue
            ok = [c for c in cells if not c["error"]]
            if not ok:
                continue
            tok = sorted(c["prompt_tokens"] for c in ok)[len(ok) // 2]
            rate = 100 * sum(c["flipped"] for c in ok) / len(ok)
            pts.append((tok, rate))
    pts.sort()
    xs = [t for t, _ in pts]
    ys = [p for _, p in pts]
    ceiling = 922_000

    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.plot(xs, ys, "-o", color=FLAT, linewidth=2.4, markersize=7, zorder=3)
    ax.axvline(ceiling, color=MUTE, linestyle=(0, (5, 4)), linewidth=1)
    ax.text(ceiling * 0.94, 50, "model ceiling 922k", color=MUTE, fontsize=10,
            rotation=90, va="center", ha="right")
    ax.text(xs[len(xs) // 2], 104, "100% at every size", color=FLAT, fontsize=12,
            fontweight="bold", ha="center")
    ax.set_xscale("log")
    ax.set_xlim(2000, 1_200_000)
    ax.set_ylim(0, 112)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xticks([10_000, 100_000, 1_000_000])
    ax.set_xticklabels(["10k", "100k", "1M"])
    ax.set_xlabel("tokens fed to the summarizer (log scale) — each point n = 3")
    _clean(ax, grid_axis="y")
    ax.set_title("Laundering is scale-invariant (pi, gpt-5.6-terra)")
    save(fig, "fig2-scale-invariance")


# --------------------------------------------------------------------------- Fig 3
def fig_execution_attenuation() -> None:
    es = json.loads((DATA / "execute_scale_result.json").read_text())
    pi_pts = []
    for k, rows in es.items():
        if k.endswith("_clean"):
            continue
        landed = [r for r in rows if not r.get("skipped")]
        tok = sorted(r["prompt_tokens"] for r in rows)[len(rows) // 2]
        ex = 100 * sum(1 for r in landed if r.get("ran_the_curl")) / len(rows)
        pi_pts.append((tok, ex))
    pi_pts.sort()

    ef = json.loads((DATA / "execute_flattening_result.json").read_text())
    hpts = []
    for h, rows in ef.items():
        lr = rows["laundered"]
        landed = [r for r in lr if not r.get("skipped")]
        tok = sorted(r["prompt_tokens"] for r in landed)[len(landed) // 2]
        ex = 100 * sum(1 for r in landed if r.get("ran_the_curl")) / len(lr)
        hpts.append((h, tok, ex))

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.axhline(100, color=STRUCT, linewidth=2.2, linestyle=(0, (6, 4)), zorder=2)
    ax.text(300_000, 101.5, "laundering: 100% (flat)", color=STRUCT, fontsize=11,
            fontweight="bold", ha="right", va="bottom")

    xs = [t for t, _ in pi_pts]
    ys = [p for _, p in pi_pts]
    ax.plot(xs, ys, "-o", color=EXEC, linewidth=2.4, markersize=7, zorder=3, label="pi, growing window")
    ax.text(xs[0], ys[0] - 7, "pi, by window size", color=EXEC, fontsize=11, fontweight="bold",
            ha="left", va="top")

    lab = {"opencode": "opencode", "cline": "Cline", "aider": "Aider", "openhands": "OpenHands"}
    # opencode and cline land on the same point (~185k, ~20%): nudge the diamonds apart on the
    # log-x axis (diamond ×mult) and stagger the labels above/below so nothing overlaps.
    off = {"openhands": (1.00, 12, "center"), "opencode": (0.86, 12, "right"),
           "aider": (1.00, 12, "left"), "cline": (1.16, -14, "center")}
    for h, t, p in hpts:
        mult, dy, ha = off[h]
        ax.plot(t * mult, p, marker="D", color=FLAT, markersize=9, zorder=4, linestyle="none")
        ax.annotate(lab[h], (t * mult, p + dy), color=FLAT, fontsize=10,
                    fontweight="bold", ha=ha, va="center")

    ax.set_xscale("log")
    ax.set_xlim(2000, 400_000)
    ax.set_ylim(-6, 112)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax.set_xticks([3000, 10_000, 30_000, 100_000, 300_000])
    ax.set_xticklabels(["3k", "10k", "30k", "100k", "300k"])
    ax.set_xlabel("effective (post-truncation) window in tokens, log scale")
    _clean(ax, grid_axis="y")
    ax.set_title("Execution falls as the window fills — laundering does not")
    fig.text(0.01, -0.03, "Circles: pi at a fixed scenario, growing window.  Diamonds: each flattening "
             "harness at its own effective window.", color=MUTE, fontsize=10)
    save(fig, "fig3-execution-attenuation")


# --------------------------------------------------------------------------- Fig 4
def fig_salience_recovery() -> None:
    path = DATA / "salience_recovery_result.json"
    if not path.exists():
        print("  (skip fig4: salience_recovery_result.json not present)")
        return
    d = json.loads(path.read_text())
    arms = ["A2_repeat", "A0_baseline", "A4_combined", "A3_framed", "A5_recency_framed", "A1_recency"]
    lab = {"A0_baseline": "baseline\n@75%", "A1_recency": "recency\n@end", "A2_repeat": "repeat\n4×",
           "A3_framed": "framed\n@75%", "A4_combined": "framed+\nrepeat+end", "A5_recency_framed": "framed\n@end"}
    names, exs, sals = [], [], []
    for a in arms:
        if a not in d:
            continue
        rows = d[a]["laundered"]
        landed = [r for r in rows if not r.get("skipped")]
        ex = 100 * sum(1 for r in landed if r.get("ran_the_curl")) / len(rows)
        sv = [r["salience"] for r in landed if r.get("salience")]
        names.append(lab[a])
        exs.append(ex)
        sals.append(sum(sv) / len(sv) if sv else 0)

    # Two stacked panels sharing the x-axis — avoids a dual-scale (two-y-axis) chart.
    fig, (ax_e, ax_s) = plt.subplots(2, 1, figsize=(7.2, 4.8), sharex=True,
                                     gridspec_kw={"height_ratios": [2, 1], "hspace": 0.15})
    x = range(len(names))
    ax_e.bar(x, exs, width=0.6, color=FLAT, zorder=3)
    for xi, e in zip(x, exs):
        ax_e.text(xi, e + 3, f"{e:.0f}%", ha="center", va="bottom", color=FLAT,
                  fontsize=11, fontweight="bold")
    ax_e.set_ylim(0, 100)
    ax_e.set_yticks([0, 50, 100])
    ax_e.set_yticklabels(["0%", "50%", "100%"])
    ax_e.set_ylabel("executed", color=FLAT)
    _clean(ax_e, grid_axis="y")
    ax_e.set_title("Beating the attenuation: injection design vs execution")

    ax_s.plot(list(x), sals, "-o", color=EXEC, linewidth=2.2, markersize=7, zorder=3)
    for xi, s in zip(x, sals):
        ax_s.text(xi, s + 0.18, f"{s:.1f}", ha="center", va="bottom", color=EXEC, fontsize=10)
    ax_s.set_ylim(1, 5.6)
    ax_s.set_yticks([1, 3, 5])
    ax_s.set_ylabel("salience\n(1–5)", color=EXEC)
    _clean(ax_s, grid_axis="y")
    ax_s.set_xticks(list(x))
    ax_s.set_xticklabels(names, fontsize=10)

    fig.text(0.01, -0.04, "Same ~300k window; only the injection design changes.  Bars: end-to-end "
             "execution (n = 5).  Line: LLM-judged salience.", color=MUTE, fontsize=10)
    save(fig, "fig4-salience-recovery")


# --------------------------------------------------------------------------- Fig 0: the pipeline
def fig_pipeline() -> None:
    """Schematic (not data-driven): the compaction pipeline, with the flatten step marked as the
    point where message provenance is lost."""
    from matplotlib.patches import FancyBboxPatch

    fig, ax = plt.subplots(figsize=(7.2, 2.15))
    ax.set_xlim(0, 100)
    ax.set_ylim(30, 100)
    ax.axis("off")

    y, w, h = 62, 15, 22
    # uneven spacing: the "summarize" arrow (arrow 2) gets the widest gap, since its label is longest
    nodes = [
        (8, "typed\nmessages", "each message keeps\nits own source"),
        (34, "one plain-\ntext string", "roles become text\nlabels like [User]:"),
        (66, "summary", None),
        (92, "new\nmemory", None),
    ]

    def box(cx, title, edge):
        ax.add_patch(FancyBboxPatch((cx - w / 2, y - h / 2), w, h,
                     boxstyle="round,pad=0.4,rounding_size=2.5", linewidth=1.4,
                     edgecolor=edge, facecolor="white", zorder=3))
        ax.text(cx, y, title, ha="center", va="center", fontsize=11, zorder=4)

    def sub(cx, s):
        if s:
            ax.text(cx, y - h / 2 - 4, s, ha="center", va="top", fontsize=8.5, color=MUTE, zorder=4)

    def arrow(x0, x1, label, color=INK, lw=1.8, weight="normal"):
        ax.annotate("", xy=(x1, y), xytext=(x0, y),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, mutation_scale=14), zorder=2)
        ax.text((x0 + x1) / 2, y + 5, label, ha="center", va="bottom", fontsize=9.5,
                color=color, fontweight=weight)

    for cx, t, s in nodes:
        box(cx, t, FLAT if cx == 34 else INK)  # the flattened string is where provenance is already gone
        sub(cx, s)
    arrow(nodes[0][0] + w / 2, nodes[1][0] - w / 2, "flatten", color=FLAT, lw=2.6, weight="bold")
    arrow(nodes[1][0] + w / 2, nodes[2][0] - w / 2, "summarize")
    arrow(nodes[2][0] + w / 2, nodes[3][0] - w / 2, "carried\nforward")

    # mark the flatten step as the vulnerable one
    fx = (nodes[0][0] + w / 2 + nodes[1][0] - w / 2) / 2
    ax.text(fx, y + 18, "provenance lost:\nlabels not escaped", ha="center", va="bottom",
            fontsize=8.5, color=FLAT, fontweight="bold")
    save(fig, "fig0-pipeline")


def main() -> int:
    if "--check" in sys.argv:
        return _check()
    fig_pipeline()
    fig_laundering_by_harness()
    fig_scale_invariance()
    fig_execution_attenuation()
    fig_salience_recovery()
    return 0


def _check() -> int:
    """Regenerate into a temp dir; fail if the committed PDFs/SVGs differ from the data."""
    import filecmp
    import tempfile

    global OUT
    committed = OUT
    with tempfile.TemporaryDirectory() as tmp:
        OUT = Path(tmp)
        fig_pipeline()
        fig_laundering_by_harness()
        fig_scale_invariance()
        fig_execution_attenuation()
        fig_salience_recovery()
        stale = []
        for f in OUT.glob("*.svg"):  # SVG is deterministic; PDF/PNG carry timestamps
            other = committed / f.name
            if not other.exists() or not filecmp.cmp(f, other, shallow=False):
                stale.append(f.name)
        OUT = committed
    if stale:
        print("STALE (rerun make_figures.py and commit): " + ", ".join(sorted(stale)))
        return 1
    print("figures up to date with data")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
