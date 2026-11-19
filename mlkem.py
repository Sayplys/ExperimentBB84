"""
ML-KEM-768 (FIPS 203) key encapsulation through liboqs, for the BB84 comparison.

Flow over a classical channel (methodology section 3.2):
    KeyGen : Bob   -> public key (1184 B) + private key (2400 B)
    Encaps : Alice -> ciphertext (1088 B) + 256-bit shared secret
    Decaps : Bob   -> 256-bit shared secret

Adversary models (section 3.3):
    passive : Eve copies the public key and the ciphertext. The traffic changes nothing.
    active  : Eve flips `tamper_bits` random bits of the ciphertext in transit.

ML-KEM uses the Fujisaki-Okamoto transform with *implicit rejection*: Decaps never
raises on a modified ciphertext. It returns a pseudo-random secret derived from the
private key instead, so the two parties simply end with different secrets. They find
out when the key is first used (e.g. a failed MAC), not inside the KEM itself.
"""

import time
from dataclasses import dataclass

import numpy as np
import oqs

ALGORITHM = "ML-KEM-768"


@dataclass
class MLKEMResult:
    public_key_bytes: int
    secret_key_bytes: int
    ciphertext_bytes: int
    secret_bits: int
    keygen_s: float
    encaps_s: float
    decaps_s: float
    tampered_bits: int
    eavesdropped: bool
    keys_match: bool                  # Alice's and Bob's secrets are equal

    @property
    def bytes_on_wire(self) -> int:
        """Traffic on the channel: public key (Bob -> Alice) + ciphertext (Alice -> Bob)."""
        return self.public_key_bytes + self.ciphertext_bytes

    @property
    def total_s(self) -> float:
        return self.keygen_s + self.encaps_s + self.decaps_s

    @property
    def aborted(self) -> bool:
        """True when the exchange yields no usable shared key."""
        return not self.keys_match


def flip_bits(data: bytes, n_bits: int, rng: np.random.Generator) -> bytes:
    """Return `data` with `n_bits` distinct random bit positions flipped."""
    out = bytearray(data)
    for pos in rng.choice(len(data) * 8, size=n_bits, replace=False):
        out[pos // 8] ^= 1 << (pos % 8)
    return bytes(out)


def run_mlkem(eavesdropper: bool = False, tamper_bits: int = 0, seed: int | None = None) -> MLKEMResult:
    """Run one KeyGen / Encaps / Decaps exchange. `tamper_bits` > 0 is the active attack."""
    rng = np.random.default_rng(seed)

    with oqs.KeyEncapsulation(ALGORITHM) as bob, oqs.KeyEncapsulation(ALGORITHM) as alice:
        t0 = time.perf_counter()
        public_key = bob.generate_keypair()
        t1 = time.perf_counter()
        ciphertext, alice_secret = alice.encap_secret(public_key)
        t2 = time.perf_counter()

        sent = flip_bits(ciphertext, tamper_bits, rng) if tamper_bits else ciphertext
        bob_secret = bob.decap_secret(sent)
        t3 = time.perf_counter()

        return MLKEMResult(
            public_key_bytes=len(public_key),
            secret_key_bytes=len(bob.export_secret_key()),
            ciphertext_bytes=len(ciphertext),
            secret_bits=8 * len(alice_secret),
            keygen_s=t1 - t0,
            encaps_s=t2 - t1,
            decaps_s=t3 - t2,
            tampered_bits=tamper_bits,
            eavesdropped=eavesdropper,
            keys_match=alice_secret == bob_secret,
        )
