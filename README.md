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

## Running

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py              # 200 photons, seed 42
.venv/bin/python main.py --n 1000 --seed 7
```

The output prints a step-by-step table of the first photons and a summary for each
scenario. It also saves these images to `figures/`:

- `scenarios_comparison.png`: both scenarios side by side, photon by photon, with their QBER
- `circuit_no_eve.png`, `circuit_with_eve.png`: 6-photon example circuits
- `qber_vs_intercept_rate.png`: measured QBER against the fraction of photons Eve
  intercepts, compared with the theoretical `rate / 4`
