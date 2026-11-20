# BB84 Quantum Key Distribution with Qiskit

A simulation of the BB84 protocol (C. H. Bennett & G. Brassard, *Quantum cryptography:
Public key distribution and coin tossing*, 1984). It runs two scenarios:

| Scenario | Expected error rate (QBER) | Outcome |
|---|---|---|
| Alice and Bob only | 0 % | Key accepted, Alice's and Bob's keys are identical |
| Eve runs an intercept-resend attack | ~25 % | Attack detected, key discarded |

## Protocol steps (as implemented in `bb84.py`)

1. **Alice** picks random bits and random bases (`+` rectilinear / `x` diagonal) and
   encodes each bit in one photon (qubit): `|0>,|1>` or `|+>,|->`.
2. **Bob** measures each photon in a random basis.
3. **Eve** (optional) measures each photon in a random basis and resends the state she
   saw. When she guesses the wrong basis (50 %), she disturbs the photon, and Bob then
   gets a random result. So each sifted bit has a 1/2 × 1/2 = **25 %** error chance.
4. **Sifting:** over the public channel Bob announces his bases. They keep only the
   positions where the bases matched (~50 %).
5. **Error estimation:** they publicly compare a random subset of the sifted bits.
   If the error rate is above the threshold (11 % by default), they abort. The chance
   that Eve goes unnoticed over `k` compared bits is `(3/4)^k`.
6. The bits that were not compared form the shared secret key.

All photons go in one circuit, which runs a single time (`shots=1`), like a real
transmission. The protocol uses only Clifford gates (X, H, measurement), so the Aer
stabilizer simulator can handle thousands of qubits.

## Noise model (methodology §3.1)

`run_bb84(..., noise_rate=e)` with `e` in 0..0.12 applies a Qiskit `NoiseModel`: half of
`e` comes from depolarization in the fibre (an `id` gate before Bob) and half from
readout error in the detectors, so the honest QBER is about `e`. The noise also affects
Eve's detector. The default `0` keeps the ideal behaviour above.

## ML-KEM-768 (methodology §3.2)

`mlkem.py` runs KeyGen / Encaps / Decaps through liboqs (`run_mlkem(tamper_bits=k)`),
and reports key/ciphertext sizes, per-step times and whether both sides got the same
256-bit secret. It needs the native `liboqs` library (>= 0.16) installed in `~/_oqs`,
where `liboqs-python` looks for it:

```bash
cmake -S liboqs -B build -GNinja -DCMAKE_INSTALL_PREFIX=$HOME/_oqs -DBUILD_SHARED_LIBS=ON \
      -DOQS_BUILD_ONLY_LIB=ON -DOQS_DIST_BUILD=ON && cmake --build build && cmake --install build
```

## Comparison BB84 vs ML-KEM-768 (methodology §3.3)

```bash
.venv/bin/python compare.py     # 20 runs x 2000 photons -> results/comparison.csv + summary table
.venv/bin/python plots.py       # figures/cmp_*.png
```

Scenarios: BB84 at 0/3/6/9/12 % noise, with and without an intercept-resend Eve; ML-KEM
baseline, passive Eve and an active Eve that flips 1 ciphertext bit. The methodology text
specifies 5 runs of 200 photons (`compare.py --n 200 --runs 5`); the default is a larger
sample because with 200 photons only about 50 bits are compared and the QBER is too noisy.

| Metric (20 runs of 2000 photons) | BB84 | ML-KEM-768 |
|---|---|---|
| Useful-bit rate (secret bits / bits sent) | 0.25 (about 500 key bits) | 0.014 (256 bits / 2272 B) |
| Bytes per exchange | about 940 (2000 qubits + sifting messages) | 2272 |
| Time per exchange | about 260 ms (Aer simulation) | about 0.05 ms |
| Under attack | QBER 25-31 %: aborts in 100 % of runs | secrets differ in 100 % of runs |
| Honest QBER at 12 % noise | 11.6 %, right at the 11 % threshold: 55 % of runs abort | not affected |

Caveats: the BB84 time is a simulation of the photons, not real hardware, so it is not a
speed comparison. Below 12 % noise no honest run aborts; at 12 % the intrinsic error is as
large as the threshold, so the abort is a coin flip. ML-KEM does not report the failure
itself (implicit rejection): the parties end with different secrets and find out when
using the key.

Figures: `cmp_qber_vs_noise.png`, `cmp_useful_rate.png`, `cmp_bytes.png`, `cmp_time.png`.

## Running

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py              # 2000 photons, seed 42 (sweep: 20 runs per point)
.venv/bin/python main.py --n 1000 --seed 7
```

The output prints a step-by-step table of the first photons and a summary for each
scenario. It also saves these images to `figures/`:

- `scenarios_comparison.png`: both scenarios side by side, photon by photon, with their QBER
- `circuit_no_eve.png`, `circuit_with_eve.png`: 6-photon example circuits
- `qber_vs_intercept_rate.png`: measured QBER against the fraction of photons Eve
  intercepts, compared with the theoretical `rate / 4`
