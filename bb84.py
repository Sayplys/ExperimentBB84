"""
BB84 quantum key distribution protocol (Bennett & Brassard, 1984) simulated with Qiskit.

Conventions
-----------
bit   : 0 or 1, the classical value Alice wants to send.
basis : 0 = rectilinear / Z basis  (+)  -> |0>, |1>
        1 = diagonal    / X basis  (x)  -> |+>, |->

Each photon is one qubit. All photons of a transmission are placed in a single
circuit (qubits never interact), and the circuit is run once (shots=1), just like
a real one-time transmission. Since the protocol only uses X, H and measurements
(Clifford operations), the stabilizer simulator handles thousands of qubits.
"""

from dataclasses import dataclass, field

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, ReadoutError, depolarizing_error

BASIS_SYMBOL = {0: "+", 1: "x"}

def make_noise_model(noise_rate: float) -> NoiseModel | None:
    """
    Noise model of a real optical link, parameterised by one intrinsic error rate.

    The rate is split evenly between the two physical sources, so that the QBER of
    an honest transmission is ~`noise_rate` (exactly e - 2(e/2)^2, e.g. 11.8 % for 12 %):
      * channel (fibre): depolarizing error on the `id` gate that models the
        propagation. Qiskit's depolarizing parameter lam replaces the qubit by the
        maximally mixed state with probability lam, which flips a measurement in
        either basis with probability lam/2. We want a flip of noise_rate/2, so
        lam = noise_rate.
      * detector (Bob): symmetric readout error, a flip with probability noise_rate/2.
    """
    if noise_rate <= 0:
        return None
    model = NoiseModel()
    model.add_all_qubit_quantum_error(depolarizing_error(noise_rate, 1), ["id"])
    flip = noise_rate / 2
    model.add_all_qubit_readout_error(ReadoutError([[1 - flip, flip], [flip, 1 - flip]]))
    return model


# --------------------------------------------------------------------------- #
# Quantum part: preparation, (optional) interception and measurement
# --------------------------------------------------------------------------- #
def encode(qc: QuantumCircuit, qubit, bit: int, basis: int) -> None:
    """Prepare `qubit` (initially |0>) in the BB84 state for (bit, basis)."""
    if bit:
        qc.x(qubit)
    if basis:
        qc.h(qubit)


def measure(qc: QuantumCircuit, qubit, clbit, basis: int) -> None:
    """Measure `qubit` in the given basis, storing the result in `clbit`."""
    if basis:
        qc.h(qubit)
    qc.measure(qubit, clbit)


def intercept_resend(qc: QuantumCircuit, qubit, clbit, basis: int) -> None:
    """
    Eve's intercept-resend attack: she measures the photon in her basis and sends
    Bob a fresh photon prepared in the state she observed.

    After a Z measurement the qubit already is |0> or |1>, which is exactly the
    photon Eve would resend in the + basis. For the x basis she rotates with H
    before measuring and with H again afterwards, turning |0>/|1> into |+>/|->.
    """
    measure(qc, qubit, clbit, basis)
    if basis:
        qc.h(qubit)


def build_circuit(alice_bits, alice_bases, bob_bases, eve_bases=None, eve_mask=None):
    """
    Build the full quantum transmission circuit.

    eve_bases : Eve's measurement bases (None means there is no eavesdropper).
    eve_mask  : boolean array, True for photons Eve intercepts (default: all).
    """
    n = len(alice_bits)
    q = QuantumRegister(n, "photon")
    bob_c = ClassicalRegister(n, "bob")
    qc = QuantumCircuit(q)

    for i in range(n):
        encode(qc, q[i], alice_bits[i], alice_bases[i])
    qc.barrier(label="Alice → channel")

    if eve_bases is not None:
        eve_c = ClassicalRegister(n, "eve")
        qc.add_register(eve_c)
        if eve_mask is None:
            eve_mask = np.ones(n, dtype=bool)
        for i in range(n):
            if eve_mask[i]:
                intercept_resend(qc, q[i], eve_c[i], eve_bases[i])
        qc.barrier(label="Eve → Bob")

    # Last stretch of fibre before Bob's detector. The explicit identity gate is where
    # the noise model attaches the depolarizing error (no-op when noise is off).
    for i in range(n):
        qc.id(q[i])
    qc.barrier(label="fibre → Bob")

    qc.add_register(bob_c)
    for i in range(n):
        measure(qc, q[i], bob_c[i], bob_bases[i])
    return qc


def run_circuit(qc: QuantumCircuit, seed=None, noise_rate: float = 0.0):
    """Run once and return {register_name: np.array of bits indexed by qubit}."""
    sim = AerSimulator(method="stabilizer", noise_model=make_noise_model(noise_rate))
    result = sim.run(qc, shots=1, memory=True, seed_simulator=seed).result()
    # Qiskit prints registers in reverse order of creation, separated by spaces,
    # and each register's bit 0 is the rightmost character.
    chunks = result.get_memory()[0].split(" ")
    names = [creg.name for creg in reversed(qc.cregs)]
    return {name: np.array([int(c) for c in reversed(bits)]) for name, bits in zip(names, chunks)}


# --------------------------------------------------------------------------- #
# Full protocol
# --------------------------------------------------------------------------- #
@dataclass
class BB84Result:
    n: int
    alice_bits: np.ndarray
    alice_bases: np.ndarray
    bob_bases: np.ndarray
    bob_bits: np.ndarray
    eve_bases: np.ndarray | None
    eve_bits: np.ndarray | None
    eve_mask: np.ndarray | None
    sifted_idx: np.ndarray            # positions where Alice's and Bob's bases match
    check_idx: np.ndarray             # sifted positions publicly compared
    key_idx: np.ndarray               # sifted positions kept as the secret key
    qber: float                       # error rate measured on the check bits
    threshold: float
    noise_rate: float
    circuit: QuantumCircuit = field(repr=False)

    @property
    def aborted(self) -> bool:
        return self.qber > self.threshold

    @property
    def alice_key(self) -> np.ndarray:
        return self.alice_bits[self.key_idx]

    @property
    def bob_key(self) -> np.ndarray:
        return self.bob_bits[self.key_idx]

    @property
    def eve_key_knowledge(self) -> float | None:
        """Fraction of the final key bits Eve guessed correctly."""
        if self.eve_bits is None or len(self.key_idx) == 0:
            return None
        return float(np.mean(self.eve_bits[self.key_idx] == self.alice_key))


def run_bb84(
    n: int,
    eavesdropper: bool = False,
    intercept_rate: float = 1.0,
    check_fraction: float = 0.5,
    threshold: float = 0.11,
    noise_rate: float = 0.0,
    seed: int | None = None,
) -> BB84Result:
    """
    Run the BB84 protocol for `n` photons.

    intercept_rate : fraction of photons Eve intercepts (if eavesdropper=True).
    check_fraction : fraction of the sifted key sacrificed to estimate the error rate.
    threshold      : maximum tolerated QBER; above it Alice and Bob abort (11 %, the
                     Shor-Preskill bound).
    noise_rate     : intrinsic channel + detector error rate, 0..0.12 (see
                     `make_noise_model`). Note the readout error also affects Eve's
                     detector: she is not a perfect eavesdropper.
    """
    rng = np.random.default_rng(seed)

    # 1. Alice chooses random bits and random bases.
    alice_bits = rng.integers(2, size=n)
    alice_bases = rng.integers(2, size=n)

    # 2. Bob chooses random bases. (Drawn before Eve's choices so that, for the same
    #    seed, Alice and Bob make identical choices with and without Eve.)
    bob_bases = rng.integers(2, size=n)

    # 3. Eve (optionally) chooses random bases for the photons she intercepts.
    eve_bases = eve_mask = None
    if eavesdropper:
        eve_bases = rng.integers(2, size=n)
        eve_mask = rng.random(n) < intercept_rate

    # 4. Bob measures (the circuit runs Alice -> [Eve] -> Bob).

    qc = build_circuit(alice_bits, alice_bases, bob_bases, eve_bases, eve_mask)
    regs = run_circuit(qc, seed=None if seed is None else int(rng.integers(2**31)), noise_rate=noise_rate)
    bob_bits = regs["bob"]
    eve_bits = None
    if eavesdropper:
        # Photons Eve did not touch remain unknown to her (-1).
        eve_bits = np.where(eve_mask, regs["eve"], -1)

    # 5. Public discussion: Bob announces his bases, Alice says which match.
    sifted_idx = np.flatnonzero(alice_bases == bob_bases)

    # 6. They publicly compare a random subset of the sifted bits.
    n_check = int(round(check_fraction * len(sifted_idx)))
    check_idx = np.sort(rng.choice(sifted_idx, size=n_check, replace=False))
    key_idx = np.setdiff1d(sifted_idx, check_idx)
    errors = np.sum(alice_bits[check_idx] != bob_bits[check_idx])
    qber = errors / n_check if n_check else 0.0

    return BB84Result(
        n=n,
        alice_bits=alice_bits,
        alice_bases=alice_bases,
        bob_bases=bob_bases,
        bob_bits=bob_bits,
        eve_bases=eve_bases,
        eve_bits=eve_bits,
        eve_mask=eve_mask,
        sifted_idx=sifted_idx,
        check_idx=check_idx,
        key_idx=key_idx,
        qber=float(qber),
        threshold=threshold,
        noise_rate=noise_rate,
        circuit=qc,
    )


def detection_probability(n_check: int, intercept_rate: float = 1.0) -> float:
    """
    Probability that Eve causes at least one error among `n_check` compared bits.
    Each intercepted sifted bit is wrong with probability 1/4 (Eve picks the wrong
    basis half the time, and then Bob gets a random result).
    """
    return 1 - (1 - intercept_rate / 4) ** n_check
