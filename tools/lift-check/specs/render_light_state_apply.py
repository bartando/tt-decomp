"""game_4320: apply a pong light state to shader globals.

Run the original state-copy helpers; snapshot every active upload lane at call
time, including beyond the first vector. Check call order/arguments and all
external writes without ignores or float tolerance. Upload callees are modelled
only as consumers: their implementation is outside this lift's scope.

Cover cached/cold/missing handles, all eight light slots, signed empty counts,
mode-2 directional selection, independent sign flags (any nonzero byte), VMX
versus scalar subnormals, overwritten w lanes, packed handles, preexisting dirty
bits, untouched count-vector lanes and counter wraparound.
"""
from liftcheck.spec import *

FUNCTION = "pongLightState_Apply"
ADDRESS = 0x82154320
SOURCE = "src/game/pong_render.cpp"
FP_CONTRACT = "off"
TRIALS = 2000

HANDLE_SLOTS = {
    "Diffuse": 0x825EBB18,
    "Position": 0x825EBAAC,
    "LightCount": 0x825EBC30,
    "LightType": 0x825EBAB0,
    "Ambient": 0x825EBC34,
}
LOOKUPS = {}


def lookup(ctx):
    name = ctx.read(ctx.r(3), 16).split(b"\0")[0].decode("ascii")
    ctx.ret(r3=LOOKUPS[name])


def capture_upload(ctx, pointer_reg, count_reg, stride):
    count = ctx.r(count_reg)
    if count & 0x80000000:
        count -= 0x100000000
    assert -32768 <= count <= 8, f"bad light count: {count}"
    # Empty/negative counts do not initialize the temporary arrays. Compare only
    # initialized lanes; the signed count itself is still compared exactly.
    ctx.rec.derefs[f"r{pointer_reg}"] = (ctx.read(ctx.r(pointer_reg), max(0, count) * stride), None)


CALLS = {
    0x8213E0A8: run(args=("r3", "r4")),
    0x8213E110: run(args=("r3", "r4")),
    0x8215A2F8: model(lookup, args=("r3", "r4")),
    0x8215A670: model(lambda ctx: capture_upload(ctx, 4, 5, 16), args=("r3", "r4", "r5")),
    0x82159908: model(lambda ctx: capture_upload(ctx, 5, 6, 4), args=("r3", "r4", "r5", "r6")),
}


def inputs(t):
    rng = t.rng
    state = t.alloc(0x220, "lights", ctype="pongLightState")
    # Ordinary finite values mixed with both zero signs, subnormal boundaries,
    # infinities and qNaNs. Different source w lanes make replacement observable.
    special = [0, 0x80000000, 1, 0x80000001, 0x007FFFFF, 0x807FFFFF,
               0x00800000, 0x80800000, 0x7F800000, 0xFF800000, 0x7FC00000]
    for i in range(8):
        light = state + i * 0x40
        for word in range(14):
            if rng.randrange(3) == 0:
                t.w32(light + 4 * word, rng.choice(special))
            else:
                t.wf32(light + 4 * word, rng.uniform(-100, 100))
        for off in (0x38, 0x39, 0x3A):
            t.w8(light + off, rng.choice([0, 0, 1, 2, 0x80, 0xFF]))
    t.floats(state + 0x200, 4, -5, 5)
    t.w16(state + 0x210, rng.choice([-32768, -1, 0, 1, 2, 3, 5, 7, 8]))
    t.w32(0x825EBBDC, rng.choice([0, 1, 2, 2, 3, 0xFFFFFFFF]))

    table = t.alloc(0x110, "shaderGlobals")
    entries = t.alloc(0x4000 * 8, "shaderEntries")
    values = t.alloc(64 * 16, "shaderValues")
    t.w32(table + 0x100, entries)
    t.w32(table + 0x108, values)
    t.w32(0x825EBC40, table)
    t.w32(0x825EBC54, rng.choice([0, 1, 0xFFFFFFFC, 0xFFFFFFFD, 0xFFFFFFFF, t.u32()]))

    LOOKUPS.clear()
    cold = rng.randrange(2) == 0
    missing = cold and rng.randrange(4) == 0
    for name, address in HANDLE_SLOTS.items():
        entry = rng.choice([0, 1, 15, 255, 0x3FFF, rng.randrange(0x4000)])
        bit = rng.choice([0, 7, 8, 255, 256, 2047, rng.randrange(2048)])
        handle = (entry << 18) | (bit << 1) | rng.randrange(2)
        if name == "Diffuse":
            handle = 0 if missing else handle | 1
        elif rng.randrange(8) == 0:
            handle = 0  # Diffuse alone is the initialization/availability sentinel.
        LOOKUPS[name] = handle
        t.w32(address, 0 if cold else handle)
        # Poison the unused high half of the slot descriptor. Keep other value
        # lanes random so a full-vector LightCount store cannot pass unnoticed.
        index = handle >> 18
        t.w32(entries + 8 * index + 4, (rng.randrange(1, 65536) << 16) | rng.randrange(64))
    t.args(r3=state)
