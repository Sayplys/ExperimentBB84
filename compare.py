"""
Experimental comparison BB84 (Qiskit) vs ML-KEM-768 (liboqs), methodology section 3.3.

Scenarios (RUNS independent runs each, seeds 0..RUNS-1):
  BB84   : noise in NOISE_LEVELS x {no Eve, intercept-resend Eve}
  ML-KEM : baseline, passive Eve (copies the traffic), active Eve (flips 1 ciphertext bit)

Metrics per run (one CSV row):
  key_bits     secret bits delivered (0 when the exchange aborted)
  channel_bits bits sent over the channel: BB84 = photons, ML-KEM = 8 * (pk + ct)
  useful_rate  key_bits / channel_bits
  bytes_total  traffic: BB84 = photons/8 (quantum) + classical sifting messages; ML-KEM = pk + ct
  time_ms      wall time of the whole exchange. BB84 is an Aer *simulation* of the
               photons, not real hardware, so it must not be read as a speed comparison.

    .venv/bin/python compare.py                 # 20 runs x 2000 photons
    .venv/bin/python compare.py --n 200 --runs 5   # the small sample of the methodology text
"""

import argparse
import csv
import math
import time
from pathlib import Path

import numpy as np

from bb84 import run_bb84
from mlkem import run_mlkem

NOISE_LEVELS = (0.0, 0.03, 0.06, 0.09, 0.12)
MLKEM_TAMPER_BITS = 1
FIELDS = ["protocol", "scenario", "noise", "run", "seed", "qber", "aborted", "key_bits",
          "channel_bits", "useful_rate", "bytes_total", "time_ms"]


def bb84_row(n: int, eve: bool, noise: float, run: int) -> dict:
    t0 = time.perf_counter()
    r = run_bb84(n, eavesdropper=eve, noise_rate=noise, seed=run)
    time_ms = (time.perf_counter() - t0) * 1e3
    key_bits = 0 if r.aborted else len(r.key_idx)
    # Classical public discussion: Bob's bases, Alice's match mask, the positions of the
    # compared bits (a mask over the sifted bits), Alice's check bits, Bob's verdict.
    classical = 2 * math.ceil(n / 8) + math.ceil(len(r.sifted_idx) / 8) + math.ceil(len(r.check_idx) / 8) + 1
    return dict(protocol="BB84", scenario="Eve" if eve else "baseline", noise=noise, run=run, seed=run,
                qber=r.qber, aborted=int(r.aborted), key_bits=key_bits, channel_bits=n,
                useful_rate=key_bits / n, bytes_total=n / 8 + classical, time_ms=time_ms)


def mlkem_row(scenario: str, run: int) -> dict:
    kwargs = {"baseline": {}, "passive Eve": {"eavesdropper": True},
              "active Eve": {"tamper_bits": MLKEM_TAMPER_BITS}}[scenario]
    t0 = time.perf_counter()
    r = run_mlkem(seed=run, **kwargs)
    time_ms = (time.perf_counter() - t0) * 1e3
    key_bits = 0 if r.aborted else r.secret_bits
    channel_bits = 8 * r.bytes_on_wire
    return dict(protocol="ML-KEM-768", scenario=scenario, noise="", run=run, seed=run,
                qber="", aborted=int(r.aborted), key_bits=key_bits, channel_bits=channel_bits,
                useful_rate=key_bits / channel_bits, bytes_total=r.bytes_on_wire, time_ms=time_ms)


def collect(n: int, runs: int) -> list[dict]:
    run_bb84(n, seed=999)          # warm-up (imports, JIT, caches): not recorded
    run_mlkem(seed=999)
    rows = []
    for noise in NOISE_LEVELS:
        for eve in (False, True):
            rows += [bb84_row(n, eve, noise, i) for i in range(runs)]
    for scenario in ("baseline", "passive Eve", "active Eve"):
        rows += [mlkem_row(scenario, i) for i in range(runs)]
    return rows


def summarize(rows: list[dict]) -> None:
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        groups.setdefault((r["protocol"], r["scenario"], r["noise"]), []).append(r)

    def ms(g, k):
        v = np.array([x[k] for x in g], dtype=float)
        return f"{v.mean():.3g}±{v.std():.2g}"

    print(f"{'protocol':<11} {'scenario':<12} {'noise':>5} | {'QBER':>11} {'abort':>6} {'key bits':>10} "
          f"{'useful rate':>13} {'bytes':>7} {'time ms':>11}")
    for (proto, scen, noise), g in groups.items():
        qber = ms(g, "qber") if proto == "BB84" else "-"
        noise_s = f"{noise:.0%}" if noise != "" else "-"
        print(f"{proto:<11} {scen:<12} {noise_s:>5} | {qber:>11} {np.mean([x['aborted'] for x in g]):>6.0%} "
              f"{ms(g, 'key_bits'):>10} {ms(g, 'useful_rate'):>13} {ms(g, 'bytes_total'):>7} {ms(g, 'time_ms'):>11}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--n", type=int, default=2000, help="photons per BB84 run")
    p.add_argument("--runs", type=int, default=20, help="independent runs per scenario")
    p.add_argument("--out", default="results/comparison.csv")
    a = p.parse_args()

    rows = collect(a.n, a.runs)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)
    summarize(rows)
    print(f"\n{len(rows)} runs saved to {out}")
    print("Note: BB84 time is an Aer simulation, not real photon hardware.")


if __name__ == "__main__":
    main()
