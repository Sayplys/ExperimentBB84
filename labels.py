"""Figure text in English (default) and Portuguese. Use `tr(key, **fmt)` after `set_lang(...)`."""

from pathlib import Path

_BASE = Path(__file__).parent / "figures"
_lang = "en"

STRINGS = {
    "en": {
        # main.py: sweep
        "sweep.theory": "Theory: QBER = rate / 4",
        "sweep.sim": "Simulated (mean ± std, {trials} runs of {n} photons)",
        "threshold": "Abort threshold ({t:.0%})",
        "sweep.x": "Fraction of photons intercepted by Eve",
        "sweep.y": "QBER (error rate on compared bits)",
        "sweep.title": "BB84: eavesdropping leaves a measurable error rate",
        # main.py: scenarios
        "row.alice_bit": "Alice: bit", "row.alice_basis": "Alice: basis", "row.photon": "Photon sent",
        "row.eve_basis": "Eve: basis", "row.eve_result": "Eve: result", "row.bob_basis": "Bob: basis",
        "row.bob_result": "Bob: result", "row.same_basis": "Same basis?", "row.agree": "Bits agree?",
        "yes": "Y",
        "no_eve_note": "no eavesdropper on the channel",
        "table.summary": "All {n} photons: {s} with the same basis, {e} of them disagree",
        "scn1": "Scenario 1: no eavesdropper",
        "scn2": "Scenario 2: Eve intercepts and resends every photon",
        "theory_eve": "Theory with Eve: 25%",
        "scn_n": "Scenario {i}",
        "aborted": "✗ Aborted\nkey discarded", "accepted": "✓ Accepted\nkey is secret",
        "qber.title": "Error rate (QBER)",
        "leg.sifted": "Same basis: bit kept after sifting",
        "leg.eve": "Eve used the wrong basis (photon disturbed)",
        "leg.error": "Bob's bit differs from Alice's (error)",
        "main.title": "BB84 with and without an eavesdropper",
        "main.sub": "First {m} photons of {n}, with the same Alice and Bob choices in both scenarios.   "
                    "+ rectilinear basis,  x diagonal basis",
        # plots.py
        "bb84_no_eve": "BB84, no Eve",
        "bb84_eve_ir": "BB84, Eve intercept-resend",
        "bb84_eve": "BB84, Eve",
        "noise_ideal": "Noise rate (ideal QBER)",
        "cmp.threshold": "Abort threshold (11%)",
        "cmp.qber.title": "BB84: Eve is visible well above the channel noise",
        "cmp.qber.x": "Intrinsic noise rate",
        "cmp.qber.y": "QBER (mean ± std, {runs} runs of {n} photons)",
        "kem_no_eve": "ML-KEM-768, no Eve",
        "kem_eve": "ML-KEM-768, Eve flips a bit",
        "cmp.rate.title": "Useful-bit rate: BB84 yields more key per bit sent",
        "cmp.rate.x": "Intrinsic noise rate (BB84 only)",
        "cmp.rate.y": "Secret bits / bits sent (mean ± std, {runs} runs)",
        "cmp.bytes.title": "Bandwidth: ML-KEM sends about {ratio:.1f}x more bytes",
        "cmp.bytes.x": "Bytes on the channel per exchange",
        "cmp.time.title": "Processing time per exchange (log scale)",
        "cmp.time.x": "Wall time (ms)",
        "cmp.time.note": "BB84 = Qiskit Aer simulation of the photons, not real hardware: not a speed comparison.",
    },
    "pt": {
        "sweep.theory": "Teoria: QBER = taxa / 4",
        "sweep.sim": "Simulado (média ± desvio, {trials} execuções de {n} fótons)",
        "threshold": "Limite de aborto ({t:.0%})",
        "sweep.x": "Fração de fótons interceptados por Eve",
        "sweep.y": "QBER (taxa de erro nos bits comparados)",
        "sweep.title": "BB84: a espionagem deixa uma taxa de erro mensurável",
        "row.alice_bit": "Alice: bit", "row.alice_basis": "Alice: base", "row.photon": "Fóton enviado",
        "row.eve_basis": "Eve: base", "row.eve_result": "Eve: resultado", "row.bob_basis": "Bob: base",
        "row.bob_result": "Bob: resultado", "row.same_basis": "Mesma base?", "row.agree": "Bits iguais?",
        "yes": "S",
        "no_eve_note": "sem espiã no canal",
        "table.summary": "Todos os {n} fótons: {s} com a mesma base, {e} deles divergem",
        "scn1": "Cenário 1: sem espiã",
        "scn2": "Cenário 2: Eve intercepta e reenvia todos os fótons",
        "theory_eve": "Teoria com Eve: 25%",
        "scn_n": "Cenário {i}",
        "aborted": "✗ Abortado\nchave descartada", "accepted": "✓ Aceito\nchave é secreta",
        "qber.title": "Taxa de erro (QBER)",
        "leg.sifted": "Mesma base: bit mantido após a peneiração",
        "leg.eve": "Eve usou a base errada (fóton perturbado)",
        "leg.error": "Bit de Bob difere do de Alice (erro)",
        "main.title": "BB84 com e sem espiã",
        "main.sub": "Primeiros {m} fótons de {n}, com as mesmas escolhas de Alice e Bob nos dois cenários.   "
                    "+ base retilínea,  x base diagonal",
        "bb84_no_eve": "BB84, sem Eve",
        "bb84_eve_ir": "BB84, Eve intercepta e reenvia",
        "bb84_eve": "BB84, com Eve",
        "noise_ideal": "Taxa de ruído (QBER ideal)",
        "cmp.threshold": "Limite de aborto (11%)",
        "cmp.qber.title": "BB84: Eve é visível bem acima do ruído do canal",
        "cmp.qber.x": "Taxa de ruído intrínseco",
        "cmp.qber.y": "QBER (média ± desvio, {runs} execuções de {n} fótons)",
        "kem_no_eve": "ML-KEM-768, sem Eve",
        "kem_eve": "ML-KEM-768, Eve inverte um bit",
        "cmp.rate.title": "Taxa de bits úteis: BB84 rende mais chave por bit enviado",
        "cmp.rate.x": "Taxa de ruído intrínseco (apenas BB84)",
        "cmp.rate.y": "Bits secretos / bits enviados (média ± desvio, {runs} execuções)",
        "cmp.bytes.title": "Banda: o ML-KEM envia cerca de {ratio:.1f}x mais bytes",
        "cmp.bytes.x": "Bytes no canal por troca",
        "cmp.time.title": "Tempo de processamento por troca (escala log)",
        "cmp.time.x": "Tempo de relógio (ms)",
        "cmp.time.note": "BB84 = simulação dos fótons no Qiskit Aer, não hardware real: não é uma comparação de velocidade.",
    },
}


def set_lang(lang: str) -> Path:
    """Select the language; returns (and creates) the output folder for the figures."""
    global _lang
    _lang = lang
    out = _BASE if lang == "en" else _BASE / lang
    out.mkdir(parents=True, exist_ok=True)
    return out


def tr(key: str, **kw) -> str:
    s = STRINGS[_lang][key]
    return s.format(**kw) if kw else s
