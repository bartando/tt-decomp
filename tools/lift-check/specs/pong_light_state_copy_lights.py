"""game_E110: copy eight lighting records, preserving padding and state tail.

The shader consumer at 0x82154320 binds Diffuse, Position, LightCount,
LightType, Ambient. The name is inferred, not an original recovered symbol.
Compare bytes exactly (including float payloads); no ignored ranges or stubs.
"""

FUNCTION = "pongLightState_CopyLights"
ADDRESS = 0x8213E110
SOURCE = "src/game/pong_render.cpp"
TRIALS = 1000

# Scalars travel through lfs/stfs; vectors are raw VMX loads/stores.
FLOAT_BITS = (0, 0x80000000, 1, 0x807FFFFF, 0x00800000, 0x7F7FFFFF,
              0xFF7FFFFF, 0x7F800000, 0xFF800000, 0x7FC12345, 0xFFC54321,
              0x7F812345, 0xFF812345)


def inputs(t):
    dst = t.alloc(0x260, "destination_with_guards") + 0x10
    src = t.alloc(0x260, "source_with_guards") + 0x10
    # Self assignment must also leave arbitrary padding and metadata intact.
    if t.rng.randrange(5) == 0:
        src = dst
    for i in range(8):
        for s in range(2):
            bits = (t.rng.choice(FLOAT_BITS) if t.rng.randrange(2)
                    else t.rng.getrandbits(32))
            t.w32(src + i * 64 + 48 + s * 4, bits)
        # Include noncanonical booleans; copying must preserve the byte.
        for f in range(4):
            t.w8(src + i * 64 + 56 + f, t.rng.choice((0, 1, 2, 0x80, 0xFF)))
    # Deliberately unrelated to the eight slots the routine always copies.
    t.w16(src + 0x210, t.rng.choice((0, 1, 7, 8, 0xFFFF, 0x8000)))
    t.w16(src + 0x212, t.rng.getrandbits(16))
    t.args(r3=dst, r4=src)
