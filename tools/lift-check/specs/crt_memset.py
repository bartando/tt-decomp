"""CRT byte fill, including its shared aligned body at 0x8242FEF0."""

FUNCTION = "memset"
ADDRESS = 0x8242FED0
SOURCE = "src/crt/memory.c"
TRIALS = 2048
# The symbol map splits the alignment prologue from the rest of the function.
# Execute the stores rather than treating memset_aligned as a modelled callee.
EXTRA_RANGES = [(0x8242FEF0, 0x8242FF70)]

SIZES = tuple(range(34)) + tuple(
    boundary + delta
    for boundary in (64, 128, 256, 512, 1024, 4096, 16384)
    for delta in (-3, -2, -1, 0, 1, 2, 3)
)


def inputs(t):
    rng = t.rng
    size = rng.choice(SIZES) if rng.randrange(4) else rng.randrange(2049)
    offset = rng.randrange(128)
    # Random guards on both ends expose under/over-writes, including zero-size calls.
    buffer = t.alloc(size + 384, "fillAndGuards", align=128)
    value = rng.choice((0, 1, 127, 128, 255, 256, -1, -256, rng.getrandbits(32)))
    t.args(r3=buffer + 128 + offset, r4=value, r5=size)
