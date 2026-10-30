"""Per-pass render defaults (the auto-name pongShadowMap_5590_g is misleading).

Exercise signed/unsigned pass boundaries, independently matching/mismatching
applied state, arbitrary dirty masks, all eight texture nibbles, null/present
shadow handles and both shadow textures. Randomize lookup order, missing keys,
duplicates and first/last entries in both fallback tables, with a sampler entry
beyond the 20-entry search. Compare all external writes exactly, without ignores.
Call-boundary snapshots catch early/late publication; reset-sampler side effects
check reloads of shadow context, format and LOD globals after the call.

The two callees are models of their boundary, not their GPU/shader internals.
This checks the image ABI and behavior, not full host linking or match playback.
"""
from liftcheck.spec import *

FUNCTION = "pongRender_ResetState"
ADDRESS = 0x82225590
SOURCE = "src/game/pong_render.cpp"
TRIALS = 1200
FP_CONTRACT = "off"

DEFAULTS, PENDING, APPLIED = 0x825C8F58, 0x825EBBD8, 0x825EBB80
TEXTURES, PENDING_TEXTURES, APPLIED_TEXTURES = 0x825C8FB0, 0x825EBB20, 0x825EBAB8
DIRTY, TEXTURE_DIRTY = 0x825EBB1C, 0x825EBAB4
RENDER_TABLE, SAMPLER_TABLE = 0x825B1F90, 0x825B2248
SHADOW, FORMAT, LOD_FLAG = 0x826063C8, 0x825C9030, 0x826064E2
RENDER_KEYS = (60, 80, 72, 76, 96, 100, 44, 40, 48, 212, 56)
SAMPLER_KEYS = (24, 16, 20, 36, 0, 4, 8, 28, 56)
_snapshots = []
_call_index = 0
_ranges = []
_after_reset = []


def boundary(name):
    def check(ctx):
        global _call_index
        state = (name, tuple(ctx.read(a, n) for a, n in _ranges))
        if ctx.side == "orig":
            _snapshots.append(state)
        else:
            assert _call_index < len(_snapshots), f"extra call: {name}"
            assert state == _snapshots[_call_index], f"state before {name} differs"
            _call_index += 1
        if name == "reset samplers":
            for address, data in _after_reset:
                ctx.write(address, data)
    return model(check, args=() if name == "reset samplers" else ("r3", "r4"))


CALLS = {
    "game_5450": boundary("reset samplers"),
    "pongShadowMap_A5C8_g": boundary("shadow texture"),
}


def fill_table(t, base, count, keys, halfword=False):
    rng = t.rng
    for i in range(count):
        # Nonkeys and untouched values/padding must survive the reset.
        if halfword:
            t.w16(base + i * 8, rng.randrange(0x10000))
            t.w16(base + i * 8 + 2, 0xFFFF)
        else:
            t.w32(base + i * 8, 0xFFFFFFFF)
        t.w32(base + i * 8 + 4, t.u32())
    slots = list(range(count))
    rng.shuffle(slots)
    for key in keys:
        if rng.randrange(4) == 0:
            continue
        slot = slots.pop()
        write = t.w16 if halfword else t.w32
        write(base + slot * 8 + (2 if halfword else 0), key)
        if rng.randrange(3) == 0:
            write(base + slots.pop() * 8 + (2 if halfword else 0), key)


def inputs(t):
    global _snapshots, _call_index, _ranges, _after_reset
    _snapshots, _call_index = [], 0
    rng = t.rng
    pass_id = rng.choice([-0x80000000, -17, -1, *range(20), 0x7FFFFFFF, t.u32()])
    for base, count in ((DEFAULTS, 22), (PENDING, 23), (APPLIED, 22),
                        (TEXTURES, 24), (PENDING_TEXTURES, 24), (APPLIED_TEXTURES, 24)):
        for i in range(count):
            t.w32(base + i * 4, rng.choice([0, 1, 2, 3, 7, 15, t.u32()]))
    t.w32(DEFAULTS - 4, t.u32())
    t.w32(DIRTY, rng.choice([0, 0xFFFFFFFF, t.u32()]))
    t.w32(TEXTURE_DIRTY, rng.choice([0, 0xFFFFFFFF, 0xEEEEEEEE, 0x11111111, t.u32()]))
    default_texture = rng.choice([0, t.alloc(32, "default texture")])
    t.w32(0x825EBA20, default_texture)
    for slot in range(8):
        t.w32(APPLIED_TEXTURES + slot * 12, rng.choice([default_texture, t.u32()]))

    holders = []
    shadow_ranges = []
    for i in range(2):
        holder = t.alloc(16, f"shadow holder {i}")
        shadow = t.alloc(1040, f"shadow map {i}")
        holders.append(holder)
        t.w32(holder + 8, shadow)
        t.w32(shadow + 1028, rng.choice([0, 0, t.u32() | 1]))
        t.w32(shadow + 976, rng.choice([0, t.alloc(32, f"shadow texture A {i}")]))
        t.w32(shadow + 980, rng.choice([0, t.alloc(32, f"shadow texture B {i}")]))
        shadow_ranges += [(holder, 16), (shadow, 1040)]
    t.w32(SHADOW, holders[0])
    t.w32(FORMAT, rng.choice([0x1A220197, 0x2D200196, t.u32()]))
    t.w8(LOD_FLAG, rng.choice([0, 1, 2, 255]))
    # Finite values keep scalar float conversion exact; signed zero is included.
    t.wf32(0x825C5938, rng.choice([-1.0, -0.0, rng.uniform(-16, 16)]))
    t.wf32(0x8202D110, rng.choice([0.0, 0.5, rng.uniform(-16, 16)]))
    fill_table(t, RENDER_TABLE, 87, RENDER_KEYS)
    fill_table(t, SAMPLER_TABLE, 20, SAMPLER_KEYS, halfword=True)
    # Entry 20 must never be searched, even when a requested key is missing.
    t.w16(SAMPLER_TABLE + 20 * 8, rng.randrange(0x10000))
    t.w16(SAMPLER_TABLE + 20 * 8 + 2, rng.choice(SAMPLER_KEYS))
    t.w32(SAMPLER_TABLE + 20 * 8 + 4, t.u32())
    _after_reset = []
    if rng.randrange(2):
        _after_reset = [
            (SHADOW, holders[1].to_bytes(4, "big")),
            (FORMAT, rng.choice([0x1A220197, 0x2D200196]).to_bytes(4, "big")),
            (LOD_FLAG, bytes([rng.choice([0, 1, 255])])),
        ]
    _ranges = [(DEFAULTS - 4, 4 + 88 + 96), (DIRTY, 4), (TEXTURE_DIRTY, 4),
               (APPLIED, 88), (PENDING, 92), (APPLIED_TEXTURES, 96),
               (PENDING_TEXTURES, 96), (RENDER_TABLE, 87 * 8 + 21 * 8),
               (SHADOW, 4), (FORMAT, 4), (LOD_FLAG, 1)] + shadow_ranges
    t.args(r3=pass_id)
