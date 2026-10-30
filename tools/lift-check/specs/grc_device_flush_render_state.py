"""Flush pending render/texture state, including device-call order and cache timing.

Covers each dirty bit, arbitrary/zero/full masks, all twelve blend presets,
out-of-range presets, packed blend factors, both format tables, all eight
texture nibbles (including nonbinding bits), default/pending/null textures,
unused-slot boundaries -1..9, null/aliased texture bindings, unsigned reference
wrap, the exact destruction mask, and callback changes to masks/state/device.
Boundary snapshots compare cache writes before calls, not just final memory.

Limits: valid readable device/context/texture pointers and table indices;
unused-slot counts are -1..9 (more negative counts are not caller inputs).
Device callbacks, texture-parameter upload and resource destruction are models:
arguments, memory at entry and scripted side effects are checked, their internal
GPU work is outside this spec. No real-match replay or concurrent host writes.
Image-address externs resolve against the game image. Host data wiring and
full application linking are not validated: the port currently defines pending
state as g_grmShaderFx_variantTable[2] and applied state as an 8-byte
g_renderTimingB, both smaller than the blocks accessed here.
No ignored memory, float tolerance, or floating arithmetic in this routine.

Run this file with --mutations to check deliberately broken build copies.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_FlushRenderState"
ADDRESS = 0x8215B138
SOURCE = "src/graphics/grc_device.cpp"
TRIALS = 1600
FP_CONTRACT = "off"
RET = None

DIRTY, TEXTURE_DIRTY = 0x825EBB1C, 0x825EBAB4
PENDING, APPLIED = 0x825EBBD8, 0x825EBB80
DEVICE = 0x825EB988
SLOTS = (136, 140, 144, 148, 152, 156, 168, 172, 176, 192, 196, 200, 308, 408)
_recorded = []
_lift_index = 0
_ranges = []
_mutate = False
_devices = []


def boundary(name):
    def check(ctx):
        global _lift_index
        snapshot = (name, tuple(ctx.read(a, n) for a, n in _ranges))
        if ctx.side == "orig":
            _recorded.append(snapshot)
        else:
            assert _lift_index < len(_recorded), f"extra call: {name}"
            assert snapshot == _recorded[_lift_index], f"state before {name} differs"
            _lift_index += 1
        if _mutate:
            if name == "texture parameter":
                # Only the first texture upload calls out; later nibbles must reload.
                ctx.write(TEXTURE_DIRTY, ctx.rng.getrandbits(32).to_bytes(4, "big"))
            elif name.startswith("state "):
                # Changes affect later groups, and the repeated +48 cache write.
                ctx.write(PENDING + 48, ctx.rng.getrandbits(32).to_bytes(4, "big"))
                ctx.write(DIRTY, ctx.rng.getrandbits(20).to_bytes(4, "big"))
                ctx.write(DEVICE, ctx.rng.choice(_devices).to_bytes(4, "big"))
            elif name == "release texture":
                ctx.write(DEVICE, ctx.rng.choice(_devices).to_bytes(4, "big"))
    args = ("r3", "r4", "r5") if name == "texture parameter" else (
        ("r3",) if name == "release texture" else ("r3", "r4"))
    return model(check, args=args)


CALLS = {f"state_{slot}": boundary(f"state {slot}") for slot in SLOTS}
CALLS.update({"hudFlashBase_A830_g": boundary("texture parameter"),
              "grcTexture_ReleaseResource": boundary("release texture")})


def inputs(t):
    global _recorded, _lift_index, _ranges, _mutate, _devices
    _recorded, _lift_index = [], 0
    rng = t.rng
    case = rng.randrange(8 * 17 * 32)
    _mutate = case % 8 == 7
    _devices = [t.alloc(0x3200, f"device{i}") for i in range(2)]
    for device in _devices:
        for slot in SLOTS:
            t.w32(device + slot, t.fake_fn(f"state_{slot}"))
    t.w32(DEVICE, _devices[0])
    for address, count in ((PENDING, 22), (APPLIED, 22), (0x825EBAB8, 24), (0x825EBB20, 24)):
        for i in range(count):
            t.w32(address + i * 4, rng.getrandbits(32))
    mode = case % 8
    dirty = (0, 0xFFFFFFFF, 1 << ((case // 8) % 32), rng.getrandbits(32),
             0xD97F9, 8, 0x40000, 0xFFFFF)[mode]
    t.w32(DIRTY, dirty)
    texture_dirty = rng.choice((0, 0xFFFFFFFF, 0x11111111, 0xEEEEEEEE,
                                1 << rng.randrange(32), rng.getrandbits(32)))
    if _mutate:
        texture_dirty |= 1
    t.w32(TEXTURE_DIRTY, texture_dirty)
    t.w8(0x825C89E5, rng.choice((0, 1, 255)))
    t.w32(0x825EB980, rng.getrandbits(32))
    t.w32(0x825EBA20, rng.choice((0, t.alloc(32, "defaultTexture"))))
    for i in range(8):
        t.w32(0x825EBB20 + i * 12, rng.choice((0, t.alloc(32, f"pendingTexture{i}"))))
    for i in (0, 16):
        t.w32(PENDING + i * 4, rng.randrange(3))
    t.w32(PENDING + 36, rng.randrange(16))
    for i in (4, 6):
        t.w32(PENDING + i * 4, rng.randrange(8))
    blend = list(range(12)) + [12, 0xFFFFFFFF, 0x4000, 0xFFFF4000,
                              (rng.getrandbits(32) | 0x4000)]
    t.w32(PENDING + 12, blend[(case // 8) % len(blend)])
    t.w32(PENDING + 72, rng.choice((-1, 0, 1, 4, 7, 8, 9)))
    t.w32(0x825C9030, rng.choice((0x1A220197, 0x2D200196, rng.getrandbits(32))))
    # Distinct nonconstant table values catch wrong index/table selections.
    for base, count in ((0x825D4CC4, 3), (0x825D4CD0, 16), (0x825D4D10, 8),
                        (0x825D4D30, 3), (0x825D4D3C, 8)):
        for i in range(count):
            t.w32(base + i * 4, rng.getrandbits(32))
    textures = []
    for i in range(9):
        texture = t.alloc(32, f"boundTexture{i}")
        # Last ref, retained ref, low-byte guard, high masked guard, ignored
        # type/high bits, and arithmetic underflow all exercise the release test.
        t.w32(texture, rng.choice((0x80000, 0x100000, 0x80001, 0x180000,
                                  0xAB080100, 0, rng.getrandbits(32))))
        textures.append(texture)
    for device in _devices:
        for slot in range(-1, 8):
            t.w32(device + (3176 + slot) * 4, rng.choice([0] + textures))
    _ranges = [(TEXTURE_DIRTY, 4), (DIRTY, 4), (PENDING, 88), (APPLIED, 88),
               (0x825EBAB8, 96), (0x825EBB20, 96), (DEVICE, 4)]
    _ranges += [(device + 12700, 36) for device in _devices]
    _ranges += [(texture, 32) for texture in textures]


MUTATIONS = [
    ("wrong texture nibble bit", [("1u << (slot * 4)", "2u << (slot * 4)")]),
    ("skip pending texture cache", [("g_grcAppliedTextureState[slot * 3] = texture;", "/* omitted */")]),
    ("wrong release mask", [("                    if ((references & 0x00F800FFu)",
                              "                    if ((references & 0x00F800FEu)")]),
    ("wrong blend preset", [("{6, 1, 1, 7, 10, 1, 10, 6, 1, 1, 1, 6}",
                             "{7, 1, 1, 7, 10, 1, 10, 6, 1, 1, 1, 6}")]),
    ("wrong packed destination", [("setState(172, factors >> 16);", "setState(172, factors & 0xFFFFu);")]),
    ("wrong format table", [("g_grcFormatId == 0x1A220197u", "g_grcFormatId != 0x1A220197u")]),
    ("cache dirty mask across callbacks", [("    auto* pending = g_grmShaderFx_variantTable;",
                                           "    const uint32_t savedDirty = g_grmShaderFx_flushRequired;\n    auto* pending = g_grmShaderFx_variantTable;"),
                                          ("g_grmShaderFx_flushRequired & 0x10000u", "savedDirty & 0x10000u")]),
    ("leave texture dirty mask set", [("    g_grmShaderFx_forceResetFlag = 0;", "    /* omitted clear */")]),
]


def main():
    import argparse
    from pathlib import Path
    from liftcheck.runner import Checker, Options
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--mutations", action="store_true")
    args = ap.parse_args()
    rc = Checker(Path(__file__), Options(seed=args.seed)).run()
    if rc:
        return rc
    if args.mutations:
        for name, patches in MUTATIONS:
            rc = Checker(Path(__file__), Options(seed=args.seed, patches=tuple(patches))).run()
            assert rc == 1, ("expected FAIL, not PASS/BUILD/SPEC/UNSUPPORTED", name, rc)
            print(f"CAUGHT {name}")
        print(f"PASS {FUNCTION}: {len(MUTATIONS)} mutations caught (seed {args.seed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
