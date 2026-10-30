"""8740: nearest-box correction and containment, including inverted bounds.

All xyz inside/outside combinations, equality, signed zero, unordered operands,
untouched w, and output aliases of every input. No memory or return exclusions.
"""
FUNCTION = "pongPlayer_ComputeBoxCorrection"
ADDRESS = 0x820E8740
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 1200
SPECIAL = [0, 0x80000000, 0x7FC00000, 0x7F800000, 0xFF800000,
           0x00000001, 0x80000001]


def inputs(t):
    rng = t.rng
    pos, lo, hi, out = [t.alloc(16, name) for name in ("pos", "min", "max", "delta")]
    for lane in range(3):
        a = rng.uniform(-20, 0)
        b = rng.uniform(0, 20)
        p = rng.choice([a, b, (a + b) / 2, a - 1, b + 1])
        if rng.random() < .2:
            a, b = b, a
        for base, val in ((pos, p), (lo, a), (hi, b)):
            t.wf32(base + lane * 4, val)
            if rng.random() < .08:
                t.w32(base + lane * 4, rng.choice(SPECIAL))
    out = rng.choice([out, out, pos, lo, hi])
    t.args(r3=pos, r4=lo, r5=hi, r6=out)
