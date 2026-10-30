"""0x821E0270 remaps a pad's button IDs, despite its pongPlayer symbol name.

IDs 0x22..0x29 use pad bytes +4/+5; 0x2A..0x31 use +6/+7. Each pair
applies two reflections in sequence, treating every nonzero byte as true.
Other signed 32-bit IDs pass through. This is a leaf: no vtable or callees
need stubbing, and the four embedded PPC jump tables run from the image.

Sample all IDs around both ranges, independent flag combinations, non-boolean
flag bytes, signed extremes, and arbitrary 32-bit IDs. The default seed's
4096 trials cover all 16 remapped IDs under all 16 boolean flag combinations.
"""

FUNCTION = "pongPlayer_0270_g"
ADDRESS = 0x821E0270
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 4096

BOUNDARY_IDS = (0, -1, -0x80000000, 0x7FFFFFFF, 0x10000022, 0x1000002A)


def inputs(t):
    rng = t.rng
    pad = t.alloc(8, "pad")
    for offset in range(4, 8):
        # Keep true/false equally likely while probing lbz's unsigned byte test.
        value = rng.choice((1, 2, 0x7F, 0x80, 0xFF, rng.randrange(1, 256)))
        t.w8(pad + offset, value if rng.getrandbits(1) else 0)
    arbitrary_id = rng.randrange(-0x80000000, 0x80000000)
    button = rng.choice((*range(0x20, 0x34), *BOUNDARY_IDS, arbitrary_id))
    t.args(r3=pad, r4=button)
