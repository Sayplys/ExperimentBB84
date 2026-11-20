"""
Reproduces the BB84 scenario of Bennett & Brassard (1984) in two settings:

  1. Alice and Bob alone on the quantum channel  -> keys agree, QBER ~ 0%
  2. Eve performing an intercept-resend attack     -> QBER ~ 25%, attack detected

It also sweeps the fraction of photons Eve intercepts to show QBER = rate / 4,
and saves the circuit diagrams and the plot into `figures/`.

Usage:  python main.py [--n 200] [--seed 42]
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from bb84 import BASIS_SYMBOL, build_circuit, detection_probability, run_bb84

FIGURES = Path(__file__).parent / "figures"


RUNS = 20          # independent runs per experiment (same as compare.py)
N_PHOTONS = 2000   # photons per BB84 run (same as compare.py)


def bits_str(bits) -> str:
    return "".join("." if b < 0 else str(b) for b in bits)


def print_table(res, limit: int = 20) -> None:
    """Step-by-step table of the first `limit` photons, in the style of the paper."""
    m = min(limit, res.n)
    cols = range(m)
    check, key = set(res.check_idx), set(res.key_idx)

    def row(label, values):
        print(f"  {label:<22}" + " ".join(f"{v:>1}" for v in values))

    row("Alice's random bits", res.alice_bits[:m])
    row("Alice's bases", [BASIS_SYMBOL[b] for b in res.alice_bases[:m]])
    if res.eve_bases is not None:
        row("Eve's bases", [BASIS_SYMBOL[b] if res.eve_mask[i] else " " for i, b in enumerate(res.eve_bases[:m])])
        row("Eve's results", [b if b >= 0 else " " for b in res.eve_bits[:m]])
    row("Bob's bases", [BASIS_SYMBOL[b] for b in res.bob_bases[:m]])
    row("Bob's results", res.bob_bits[:m])
    row("Same basis?", ["Y" if res.alice_bases[i] == res.bob_bases[i] else " " for i in cols])
    row("Use (C=check, K=key)", ["C" if i in check else "K" if i in key else " " for i in cols])
    row("Check errors", ["X" if i in check and res.alice_bits[i] != res.bob_bits[i] else " " for i in cols])
    if res.n > m:
        print(f"  ... ({res.n - m} more photons)")


def report(title: str, res) -> None:
    print("=" * 70)
    print(title)
    print("=" * 70)
    print_table(res)
    n_check = len(res.check_idx)
    mismatches = int(np.sum(res.alice_key != res.bob_key))
    print()
    print(f"  Photons sent               : {res.n}")
    print(f"  Sifted bits (same basis)   : {len(res.sifted_idx)}  (~50% expected)")
    print(f"  Bits publicly compared     : {n_check}")
    print(f"  QBER on compared bits      : {res.qber:.1%}  (threshold {res.threshold:.0%})")
    print(f"  Remaining key length       : {len(res.key_idx)}")
    print(f"  Alice key : {bits_str(res.alice_key[:48])}{'...' if len(res.key_idx) > 48 else ''}")
    print(f"  Bob key   : {bits_str(res.bob_key[:48])}{'...' if len(res.key_idx) > 48 else ''}")
    print(f"  Key bits that disagree     : {mismatches}")
    if res.eve_bits is not None:
        print(f"  Eve's correct key bits     : {res.eve_key_knowledge:.1%}")
        print(f"  P(detect Eve | {n_check} checks) : {detection_probability(n_check):.10f}")
    verdict = "ABORT - eavesdropper detected, key discarded" if res.aborted else "OK - key accepted"
    print(f"  Result                     : {verdict}\n")


def save_circuits(seed: int) -> None:
    """Draw a small 6-photon example of each scenario."""
    rng = np.random.default_rng(seed)
    bits, a_bases, b_bases, e_bases = (rng.integers(2, size=6) for _ in range(4))
    for name, eve in (("no_eve", None), ("with_eve", e_bases)):
        qc = build_circuit(bits, a_bases, b_bases, eve_bases=eve)
        qc.draw("mpl", fold=-1).savefig(FIGURES / f"circuit_{name}.png", dpi=150, bbox_inches="tight")
        plt.close("all")


def sweep_intercept_rate(n: int, seed: int, threshold: float, trials: int = RUNS) -> None:
    """QBER as a function of the fraction of photons Eve intercepts."""
    rates = np.linspace(0, 1, 11)
    qbers = np.array([
        [run_bb84(n, eavesdropper=True, intercept_rate=r, seed=seed + 100 * t + i).qber for t in range(trials)]
        for i, r in enumerate(rates)
    ])

    fig, ax = plt.subplots(figsize=(7, 4.2))
    surface, ink, muted = "#fcfcfb", "#0b0b0b", "#52514e"
    fig.patch.set_facecolor(surface)
    ax.set_facecolor(surface)

    ax.plot(rates, rates / 4, color="#eb6834", lw=2, ls="--", label="Theory: QBER = rate / 4")
    ax.errorbar(rates, qbers.mean(axis=1), yerr=qbers.std(axis=1), fmt="o", ms=7, color="#2a78d6",
                ecolor="#2a78d6", elinewidth=1.5, capsize=3, mec=surface, mew=2,
                label=f"Simulated (mean ± std, {trials} runs of {n} photons)")
    ax.axhline(threshold, color=muted, lw=1, ls=":")
    ax.text(0.01, threshold + 0.006, f"Abort threshold ({threshold:.0%})", color=muted, fontsize=9)

    ax.set_xlabel("Fraction of photons intercepted by Eve", color=ink)
    ax.set_ylabel("QBER (error rate on compared bits)", color=ink)
    ax.set_title("BB84: eavesdropping leaves a measurable error rate", color=ink, loc="left")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax.set_xlim(-0.03, 1.03)
    ax.set_ylim(0, 0.35)
    ax.grid(color="#e4e3df", lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(muted)
    ax.tick_params(colors=muted)
    ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0, 0.93), labelcolor=ink)

    fig.tight_layout()
    fig.savefig(FIGURES / "qber_vs_intercept_rate.png", dpi=150)
    plt.close(fig)


def plot_scenarios(res_clean, res_eve, limit: int = 20) -> None:
    """Side-by-side view of both scenarios: the first photons step by step, plus the QBER."""
    from matplotlib.patches import Patch, Rectangle

    surface, ink, muted, grid = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
    blue, orange = "#2a78d6", "#eb6834"
    sifted_bg, eve_bg, error_bg, error_ink = "#deebfb", "#fbe3d8", "#f6cfcf", "#b42b2b"
    kets = {(0, 0): "|0⟩", (1, 0): "|1⟩", (0, 1): "|+⟩", (1, 1): "|−⟩"}
    rows = ["Alice: bit", "Alice: basis", "Photon sent", "Eve: basis", "Eve: result",
            "Bob: basis", "Bob: result", "Same basis?", "Bits agree?"]
    label_w = 3.2  # width of the row-label column, in cell units

    fig = plt.figure(figsize=(15, 9.5))
    fig.patch.set_facecolor(surface)
    gs = fig.add_gridspec(2, 2, width_ratios=[4.2, 1], hspace=0.28, wspace=0.08)

    def draw_table(ax, res, title, color):
        m = min(limit, res.n)
        ax.set_xlim(-label_w, m)
        ax.set_ylim(len(rows), -1.2)
        ax.axis("off")
        ax.set_title(title, loc="left", color=ink, fontsize=13, fontweight="bold")
        ax.add_patch(Rectangle((-label_w, -1.15), 0.12, len(rows) + 1.1, color=color, clip_on=False))

        for i in range(m):
            a_bit, a_basis, b_basis, b_bit = (res.alice_bits[i], res.alice_bases[i],
                                              res.bob_bases[i], res.bob_bits[i])
            sifted = a_basis == b_basis
            if sifted:
                ax.add_patch(Rectangle((i + 0.04, -0.5), 0.92, len(rows), color=sifted_bg, lw=0))
            ax.text(i + 0.5, -0.85, str(i + 1), ha="center", va="center", color=muted, fontsize=8)

            cells = [str(a_bit), BASIS_SYMBOL[a_basis], kets[(a_bit, a_basis)], None, None,
                     BASIS_SYMBOL[b_basis], str(b_bit), "Y" if sifted else "", ""]
            if res.eve_bases is not None and res.eve_mask[i]:
                cells[3], cells[4] = BASIS_SYMBOL[res.eve_bases[i]], str(res.eve_bits[i])
                if res.eve_bases[i] != a_basis:  # wrong basis: Eve disturbed this photon
                    ax.add_patch(Rectangle((i + 0.08, 3.08), 0.84, 1.84, color=eve_bg, lw=0))
            if sifted:
                agree = a_bit == b_bit
                cells[8] = "✓" if agree else "✗"
                if not agree:
                    ax.add_patch(Rectangle((i + 0.08, 6.08), 0.84, 0.84, color=error_bg, lw=0))
                    ax.add_patch(Rectangle((i + 0.08, 8.08), 0.84, 0.84, color=error_bg, lw=0))

            for r, txt in enumerate(cells):
                if txt:
                    bad = r in (6, 8) and sifted and a_bit != b_bit
                    ax.text(i + 0.5, r + 0.5, txt, ha="center", va="center", fontsize=11,
                            color=error_ink if bad else ink, fontweight="bold" if bad else "normal")

        for r, label in enumerate(rows):
            ax.text(-label_w + 0.35, r + 0.5, label, ha="left", va="center", color=ink, fontsize=11)
        for y in (3, 5, 7):  # separate Alice / Eve / Bob / public discussion
            ax.plot([-label_w + 0.3, m], [y, y], color=grid, lw=1)
        if res.eve_bases is None:
            ax.text(m / 2, 4, "no eavesdropper on the channel", ha="center", va="center",
                    color=muted, fontsize=11, style="italic")

        errors = int(np.sum(res.alice_bits[res.sifted_idx] != res.bob_bits[res.sifted_idx]))
        ax.text(m, -1.55, f"All {res.n} photons: {len(res.sifted_idx)} with the same basis, "
                          f"{errors} of them disagree", ha="right", va="center", color=muted, fontsize=10)

    draw_table(fig.add_subplot(gs[0, 0]), res_clean, "Scenario 1: no eavesdropper", blue)
    draw_table(fig.add_subplot(gs[1, 0]), res_eve, "Scenario 2: Eve intercepts and resends every photon", orange)

    # QBER summary, shared by both scenarios
    ax = fig.add_subplot(gs[:, 1].subgridspec(2, 1, height_ratios=[10, 1.2])[0])
    ax.set_facecolor(surface)
    qbers = [res_clean.qber, res_eve.qber]
    ax.bar([0, 1], qbers, width=0.6, color=[blue, orange])
    ax.axhline(res_clean.threshold, color=muted, lw=1, ls=":")
    ax.text(-0.5, res_clean.threshold + 0.004, f"Abort threshold ({res_clean.threshold:.0%})",
            ha="left", va="bottom", color=muted, fontsize=9)
    ax.axhline(0.25, color=muted, lw=1, ls="--", alpha=0.6)
    ax.text(-0.5, 0.256, "Theory with Eve: 25%", ha="left", va="bottom", color=muted, fontsize=9)
    for x, (q, res) in enumerate(zip(qbers, (res_clean, res_eve))):
        ax.text(x, q + 0.005, f"{q:.1%}", ha="center", va="bottom", color=ink, fontsize=12, fontweight="bold")
        verdict = "✗ Aborted\nkey discarded" if res.aborted else "✓ Accepted\nkey is secret"
        ax.text(x, -0.012, f"Scenario {x + 1}", ha="center", va="top", color=ink, fontsize=11, fontweight="bold")
        ax.text(x, -0.03, verdict, ha="center", va="top", color=ink, fontsize=10)
    ax.set_xticks([])
    ax.set_xlim(-0.55, 1.55)
    ax.set_ylim(0, 0.33)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.tick_params(axis="y", colors=muted)
    ax.set_title("Error rate (QBER)",
                 loc="left", color=ink, fontsize=12, fontweight="bold")
    ax.grid(axis="y", color=grid, lw=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(muted)

    fig.legend(
        handles=[Patch(color=sifted_bg, label="Same basis: bit kept after sifting"),
                 Patch(color=eve_bg, label="Eve used the wrong basis (photon disturbed)"),
                 Patch(color=error_bg, label="Bob's bit differs from Alice's (error)")],
        loc="lower left", bbox_to_anchor=(0.02, 0.0), ncol=3, frameon=False, fontsize=10, labelcolor=ink,
    )
    fig.text(0.02, 0.965, "BB84 with and without an eavesdropper", color=ink, fontsize=16, fontweight="bold")
    fig.text(0.02, 0.94, f"First {min(limit, res_clean.n)} photons of {res_clean.n}, with the same "
                         "Alice and Bob choices in both scenarios.   + rectilinear basis,  x diagonal basis",
             color=muted, fontsize=10.5)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.07)
    fig.savefig(FIGURES / "scenarios_comparison.png", dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--n", type=int, default=N_PHOTONS, help="number of photons Alice sends")
    parser.add_argument("--seed", type=int, default=42, help="random seed (for reproducible runs)")
    parser.add_argument("--threshold", type=float, default=0.11, help="maximum tolerated QBER")
    parser.add_argument("--noise", type=float, default=0.0,
                        help="intrinsic channel+detector error rate, 0..0.12 (default 0 = ideal)")
    args = parser.parse_args()

    FIGURES.mkdir(exist_ok=True)

    res_clean = run_bb84(args.n, eavesdropper=False, threshold=args.threshold, noise_rate=args.noise, seed=args.seed)
    res_eve = run_bb84(args.n, eavesdropper=True, threshold=args.threshold, noise_rate=args.noise, seed=args.seed)
    report("SCENARIO 1 - No eavesdropper", res_clean)
    report("SCENARIO 2 - Eve intercepts and resends every photon", res_eve)

    print("Generating figures...")
    plot_scenarios(res_clean, res_eve)
    save_circuits(args.seed)
    sweep_intercept_rate(args.n, args.seed, args.threshold)
    print(f"Saved to {FIGURES}/")


if __name__ == "__main__":
    main()
