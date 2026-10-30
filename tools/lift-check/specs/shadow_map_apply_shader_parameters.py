"""0x82147228: upload shadow weights, matrices, textures and sampling parameters.

Exact comparison, no ignored memory. Consumers snapshot every descriptor-consumed
vector/matrix, including later elements. Texture selection runs the original leaf;
uploads and texture dimensions are controlled models, with calls checked in order.

Covers passes 0/1/2, signed empty counts, filtering/compaction, slots 5/6 and active
player/mode gates, raw enabled bytes, optional handles, signed tap-handle guard
(including zero), fallback texture substitution, repeated virtual dimension calls,
non-square dimensions, scalar subnormals, fused sampling taps, packed dirty bits,
full softness versus single-lane blend stores, scratch preservation and counter wrap.

Contract: at most three matching slots; descriptor lengths consume initialized
data only (the helper clamps requested counts to descriptor sizes). Map-pass
matrices are never initialized, so their descriptor length is zero. Player taps
require both primary texture bindings. Missing bindings with taps enabled read
uninitialized original stack data and have no reproducible result. Pointers are
aligned/disjoint; invalid pointers, signaling NaNs and finite overflow are excluded.
"""
import struct
from liftcheck.spec import *

FUNCTION = "pongShadowMap::applyShaderParameters"
ADDRESS = 0x82147228
SOURCE = "src/game/pong_render.cpp"
FP_CONTRACT = "off"
TRIALS = 1000


def u32(ctx, address):
    return struct.unpack(">I", ctx.read(address, 4))[0]


def capture(ctx, matrix=False):
    table = u32(ctx, 0x825EBC40)
    handle = ctx.r(4 if matrix else 3)
    entries = u32(ctx, table + 0x100)
    length = (u32(ctx, entries + (handle >> 18) * 8) >> 2) & 0x3FFF
    requested = ctx.r(6 if matrix else 5)
    assert requested <= 4, f"invalid upload count {requested}"
    size = min(length, requested) * (64 if matrix else 16)
    register = 5 if matrix else 4
    # Replace the default first-element deref, including with an empty snapshot
    # for a zero-length descriptor. Still compare requested count and pointer.
    ctx.rec.derefs[f"r{register}"] = (ctx.read(ctx.r(register), size), None)


def dimension(ctx, offset):
    ctx.ret(r3=u32(ctx, ctx.r(3) + offset))


CALLS = {
    0x821453C8: run(args=("r3", "r4", "r5")),
    0x8215A670: model(capture, args=("r3", "r4", "r5")),
    0x82159AA0: model(lambda ctx: capture(ctx, True), args=("r3", "r4", "r5", "r6")),
    0x8215A5C8: stub(ret="void", args=("r3", "r4")),
    "shadowTexture.vfn_8": model(lambda ctx: dimension(ctx, 4), args=("r3",)),
    "shadowTexture.vfn_9": model(lambda ctx: dimension(ctx, 8), args=("r3",)),
}


def inputs(t):
    rng = t.rng
    shadow = t.alloc(0x464, "shadow")
    config = t.alloc(0x800, "config")
    t.w32(shadow + 8, config)
    render_pass = rng.choice([0, 1, 2])
    mode = rng.choice([-1, 0, 1, 2, 3])
    active = rng.choice([-1, 0, 1, 2])
    t.w32(shadow + 1092, mode)
    t.w32(shadow + 1096, active)
    count = rng.choice([-3, -1, 0, 1, 3, 5, 6, 7, 7, 7])
    t.w32(config + 256, count)
    # Real slot grouping, mixed with unrelated pass IDs and shuffled matches.
    groups = [0, 0, 0, 1, 2, 1, 2]
    if rng.randrange(3) == 0:
        rng.shuffle(groups)
    matching = sum(group == render_pass for group in groups[:max(0, count)])
    for i, group in enumerate(groups):
        slot = config + 272 + 224 * i
        t.w8(slot, rng.choice([0, 0, 1, 2, 0x80, 0xFF]))
        t.w32(slot + 212, group)
        # Distinct matrices with arbitrary fourth lanes, including opaque bits.
        for word in range(16):
            t.w32(slot + 80 + 4 * word, t.u32())
        for lane in range(4):
            if rng.randrange(5) == 0:
                t.w32(slot + 144 + 4 * lane, rng.choice(
                    [0, 0x80000000, 1, 0x80000001, 0x007FFFFF, 0x00800000]))
            else:
                t.wf32(slot + 144 + 4 * lane, rng.uniform(-4, 4))
        t.wf32(slot + 208, rng.uniform(-10, 10))
    t.wf32(config + 2032, rng.uniform(-8, 8))
    t.wf32(config + 2036, rng.uniform(-8, 8))

    vtable = t.vtable("shadowTexture")
    textures = []
    for i in range(6):
        texture = t.alloc(16, f"texture{i}")
        t.w32(texture, vtable)
        t.w32(texture + 4, rng.choice([1, 3, 127, 256, 1023, 2048, rng.randint(1, 4096)]))
        t.w32(texture + 8, rng.choice([1, 7, 64, 511, 1024, 4096, rng.randint(1, 4096)]))
        textures.append(texture)
    t.w32(0x825EBA20, textures[0])
    for offset, texture in [(976, textures[1]), (1008, textures[2]),
                            (1012, textures[3]), (1016, textures[5]), (1020, textures[4])]:
        t.w32(shadow + offset, texture)
    # game_53C8's mode>=2 nonactive-player branch reads these pointers.
    for player in range(2):
        t.w32(shadow + 992 + player * 8, textures[5])

    table = t.alloc(0x110, "shaderTable")
    entries = t.alloc(0x4000 * 8, "shaderEntries")
    values = t.alloc(64 * 16, "shaderValues")
    t.w32(table + 0x100, entries)
    t.w32(table + 0x108, values)
    t.w32(0x825EBC40, table)
    t.w32(0x825EBC54, rng.choice([0, 1, 0xFFFFFFFE, 0xFFFFFFFF, t.u32()]))
    # Include handle zero (valid for the signed tap guard), all dirty-bit lanes,
    # byte boundaries and high entry indices; keep descriptor lengths independent.
    used_entries = {0}
    def handle(length, zero_allowed=False, signed=False):
        if zero_allowed and rng.randrange(4) == 0:
            value = 0
        elif signed and rng.randrange(4) == 0:
            return rng.choice([0x80000000, 0xFFFFFFFF])
        else:
            entry = rng.choice([1, 255, 0x1FFF, rng.randrange(1, 0x2000)])
            while entry in used_entries:
                entry = rng.randrange(1, 0x2000)
            used_entries.add(entry)
            bit = rng.choice([0, 7, 8, 255, 256, 2047, rng.randrange(2048)])
            value = (entry << 18) | (bit << 1) | rng.randrange(2)
        t.w32(entries + (value >> 18) * 8, length << 2)
        t.w32(entries + (value >> 18) * 8 + 4, (rng.randrange(1, 65536) << 16) | rng.randrange(64))
        return value

    bindings = {}
    for offset in (1032, 1036, 1040, 1044):
        bindings[offset] = handle(1, zero_allowed=True)
        t.w32(shadow + offset, bindings[offset])
    t.w32(shadow + 1052, handle(1, zero_allowed=True))
    weights = handle(matching, zero_allowed=True)
    t.w32(shadow + 1056, weights)
    t.w32(shadow + 1060, handle(min(matching, 2) if render_pass > 0 else 0, zero_allowed=True))
    taps = handle(4, zero_allowed=True, signed=True)
    # Handle 0 is only observed by the taps upload; earlier fields skip zero.
    t.w32(entries, 4 << 2)
    t.w32(entries + 4, (rng.randrange(1, 65536) << 16) | rng.randrange(64))
    # Don't consume taps on the original's undefined-scratch path.
    if render_pass > 0 and (bindings[1032] == 0 or bindings[1040] == 0):
        taps = 0xFFFFFFFF
    t.w32(shadow + 1068, taps)
    t.w32(shadow + 1072, handle(1, zero_allowed=True))
    # Randomize the image-backed scratch's other lanes and the sampling kernel.
    for i in range(4):
        t.w32(0x82617DF0 + i * 4, t.u32())
    for i in range(16):
        t.wf32(0x825CA4A8 + i * 4, rng.uniform(-4, 4))
    t.wf32(0x825CA430, rng.uniform(-1, 1))
    t.wf32(0x825CA434, rng.uniform(-1, 1))
    t.args(r3=shadow, r4=render_pass)
