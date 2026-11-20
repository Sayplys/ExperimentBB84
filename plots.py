"""
Figures for the BB84 vs ML-KEM-768 comparison (methodology section 3.3).
Reads results/comparison.csv (written by compare.py) and writes figures/cmp_*.png.

Colour = protocol (blue BB84, orange ML-KEM); line style = scenario (solid baseline,
dashed under attack), so colour never has to carry two meanings.

    .venv/bin/python plots.py [--lang pt]
"""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from labels import set_lang, tr

SURFACE, INK, MUTED, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BB84_C, KEM_C = "#2a78d6", "#eb6834"
THRESHOLD = 0.11
FIGURES = Path(__file__).parent / "figures"


def load(path: Path) -> list[dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


def stat(rows, key, **match):
    """(mean, std) of `key` over the rows whose columns equal `match`."""
    v = np.array([float(r[key]) for r in rows if all(r[k] == str(m) for k, m in match.items())])
    return v.mean(), v.std()


def series(rows, key, protocol, scenario):
    """Mean and std of `key` per noise level, for a BB84 scenario."""
    rows = [r for r in rows if r["protocol"] == protocol]
    noises = sorted({float(r["noise"]) for r in rows})
    ms = [stat([r for r in rows if float(r["noise"]) == nz], key, protocol=protocol, scenario=scenario)
          for nz in noises]
    return np.array(noises), np.array([m for m, _ in ms]), np.array([s for _, s in ms])


def style(ax, title, xlabel=None, ylabel=None, pct_y=False):
    ax.figure.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    ax.set_title(title, color=INK, loc="left")
    if xlabel:
        ax.set_xlabel(xlabel, color=INK)
    if ylabel:
        ax.set_ylabel(ylabel, color=INK)
    if pct_y:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.grid(color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=MUTED)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIGURES / name, dpi=150, facecolor=SURFACE)
    plt.close(fig)
    print("saved", FIGURES / name)


def line(ax, x, m, s, color, ls, label, hollow=False):
    ax.errorbar(x, m, yerr=s, color=color, ls=ls, lw=2, marker="o", ms=7, capsize=3, elinewidth=1.5,
                mfc=SURFACE if hollow else color, mec=color, mew=2, label=label)


def fig_qber(rows, n, runs):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for scen, ls, hollow, label in (("baseline", "-", False, tr("bb84_no_eve")),
                                    ("Eve", "--", True, tr("bb84_eve_ir"))):
        x, m, s = series(rows, "qber", "BB84", scen)
        line(ax, x, m, s, BB84_C, ls, label, hollow)
    ax.plot([0, 0.12], [0, 0.12], color=MUTED, lw=1, ls=":", label=tr("noise_ideal"))
    ax.axhline(THRESHOLD, color=MUTED, lw=1, ls=":")
    ax.text(0.0005, THRESHOLD + 0.006, tr("cmp.threshold"), color=MUTED, fontsize=9)
    style(ax, tr("cmp.qber.title"), tr("cmp.qber.x"),
          tr("cmp.qber.y", runs=runs, n=n), pct_y=True)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax.set_ylim(0, 0.4)
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=3, labelcolor=INK, fontsize=9)
    save(fig, "cmp_qber_vs_noise.png")


def fig_useful_rate(rows, n, runs):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for scen, ls, hollow, label in (("baseline", "-", False, tr("bb84_no_eve")),
                                    ("Eve", "--", True, tr("bb84_eve"))):
        x, m, s = series(rows, "useful_rate", "BB84", scen)
        line(ax, x, m, s, BB84_C, ls, label, hollow)
    for scen, ls, label in (("baseline", "-", tr("kem_no_eve")), ("active Eve", "--", tr("kem_eve"))):
        m, _ = stat(rows, "useful_rate", protocol="ML-KEM-768", scenario=scen)
        ax.axhline(m, color=KEM_C, lw=2, ls=ls, label=f"{label} ({m:.3f})")
    style(ax, tr("cmp.rate.title"), tr("cmp.rate.x"),
          tr("cmp.rate.y", runs=runs))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax.set_ylim(-0.02, 0.4)
    ax.legend(frameon=False, loc="upper right", labelcolor=INK, fontsize=9)
    save(fig, "cmp_useful_rate.png")


def bars(rows, key, title, xlabel, name, fmt, log=False, note=None):
    fig, ax = plt.subplots(figsize=(7, 3.1))
    vals = [(stat(rows, key, protocol=p, scenario="baseline")[0], c, p)
            for p, c in (("BB84", BB84_C), ("ML-KEM-768", KEM_C))]
    for i, (v, c, p) in enumerate(vals):
        ax.barh(i, v, color=c, height=0.5)
        ax.text(v * 1.08 if log else v + max(x for x, _, _ in vals) * 0.015, i, fmt(v), va="center", color=INK)
    ax.set_yticks(range(2), [p for _, _, p in vals], color=INK)
    ax.invert_yaxis()
    style(ax, title, xlabel)
    ax.grid(axis="y", visible=False)
    if log:
        ax.set_xscale("log")
        ax.set_xlim(right=max(v for v, _, _ in vals) * 8)
    else:
        ax.set_xlim(right=max(v for v, _, _ in vals) * 1.18)
    if note:
        ax.text(0, -0.42, note, transform=ax.transAxes, color=MUTED, fontsize=8)
    save(fig, name)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default="results/comparison.csv")
    p.add_argument("--lang", choices=("en", "pt"), default="en", help="figure language (pt -> figures/pt/)")
    a = p.parse_args()
    rows = load(Path(a.csv))
    global FIGURES
    FIGURES = set_lang(a.lang)
    runs = len({r["run"] for r in rows})
    n = round(float(next(r["channel_bits"] for r in rows if r["protocol"] == "BB84")))

    fig_qber(rows, n, runs)
    fig_useful_rate(rows, n, runs)
    ratio = stat(rows, "bytes_total", protocol="ML-KEM-768", scenario="baseline")[0] / \
        stat(rows, "bytes_total", protocol="BB84", scenario="baseline")[0]
    bars(rows, "bytes_total", tr("cmp.bytes.title", ratio=ratio), tr("cmp.bytes.x"),
         "cmp_bytes.png", lambda v: f"{v:,.0f} B")
    bars(rows, "time_ms", tr("cmp.time.title"), tr("cmp.time.x"), "cmp_time.png",
         lambda v: f"{v:.2g} ms", log=True,
         note=tr("cmp.time.note"))


if __name__ == "__main__":
    main()
