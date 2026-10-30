"""Scissor packets: direct and tiled paths, signed clipping, packing and refills.

Randomized devices cover each of the five render-target mismatches, zero target
wildcards, disabled tiling, empty tile lists, intersections/touching/disjoint or
inverted rectangles, signed extremes, coordinate truncation and offset negation.
Tile counts through 33 also exercise slw's zero and wrapped shift cases beyond
the normal 15-tile layout (the overlapping input words remain readable).

The refill helper is modeled, not executed: compare its incoming cursor/dirty
state, move to a fresh buffer and return the new last-written-word cursor.
All command bytes, final cursor, dirty bits and helper calls compare exactly.
Run this file with --mutations to check deliberately broken build copies.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_SetScissorRect"
ADDRESS = 0x823537B0
SOURCE = "src/graphics/grc_device.cpp"
TRIALS = 2000
RET = None


def refill(ctx):
    device = ctx.r(3)
    # The caller must publish the cursor before a mid-loop refill. Comparing at
    # call time catches a missing publication even though this model replaces it.
    ctx.rec.derefs["r3"] = (ctx.read(device, 40), None)
    cursor = ctx.alloc(4096)
    ctx.write(device, cursor.to_bytes(4, "big"))
    # Exercise repeated refills as well as continuing in one replacement buffer.
    limit = cursor + ctx.rng.choice([0, 32, 64, 4092])
    ctx.write(device + 8, limit.to_bytes(4, "big"))
    ctx.ret(r3=cursor)


CALLS = {0x8235A980: model(refill, args=("r3",))}


def inputs(t):
    rng = t.rng
    device = t.alloc(14032, "device")
    commands = t.alloc(4096, "commands")
    t.w32(device, commands)
    # Below, at and beyond a boundary, including exactly one tile packet.
    t.w32(device + 8, commands + rng.choice([-4, 0, 16, 28, 32, 64, 4092]))
    t.w64(device + 32, rng.choice([0, 0xFFFFFFFFFFFFC7FF, rng.getrandbits(64)]))

    mode = rng.randrange(8)
    flags = rng.randrange(256)
    t.w8(device + 10432, flags & ~0x10 if mode == 0 else flags | 0x10)
    for i in range(5):
        target = rng.choice([0, t.u32() | 1])
        counterpart = target if target != 0 else t.u32()
        if mode == i + 1:
            target = t.u32() | 1
            counterpart = target ^ 0x80000000
        t.w32(device + 12536 + 4 * i, target)
        t.w32(device + 12976 + 4 * i, counterpart)

    t.w32(device + 12960, rng.choice([0, 1, 0xFFFFFFFF, t.u32()]))
    count = rng.choice([0, 1, 2, 3, 5, 15, 16, 17, 32, 33])
    t.w32(device + 12996, count)
    limits = [-0x80000000, -32769, -16385, -1, 0, 1, 16383, 16384,
              32767, 32768, 0x7FFFFFFF]
    request = rng.choice([(10, 20, 100, 200), (-100, -200, 100, 200),
                          (0, 0, 0, 0), (100, 200, 10, 20),
                          (-0x80000000, -0x80000000, 0x7FFFFFFF, 0x7FFFFFFF),
                          tuple(rng.choice(limits) for _ in range(4)),
                          tuple(rng.randrange(-100000, 100001) for _ in range(4))])
    left, top, right, bottom = request
    rectangles = [request, (-0x80000000, -0x80000000, 0x7FFFFFFF, 0x7FFFFFFF),
                  (right, top, right, bottom), (left, bottom, right, bottom),
                  (1000, 1000, 2000, 2000), (30, 40, 60, 80),
                  (-200, -300, 50, 90), (200, 300, -200, -300)]
    for i in range(count):
        rect = rng.choice(rectangles + [tuple(rng.choice(limits) for _ in range(4))])
        for j, value in enumerate(rect):
            t.w32(device + 13000 + i * 16 + j * 4, value)
    for i in range(count):
        for j in range(2):
            t.w32(device + 13240 + i * 16 + j * 4, rng.choice(limits + [t.u32()]))
    t.args(r3=device, r4=left, r5=top, r6=right, r7=bottom)


MUTATIONS = [
    ("use 15-bit scissor coordinates", [("& 0x3FFFu", "& 0x7FFFu")]),
    ("ignore the fifth target mismatch", [("tiled && i < 5", "tiled && i < 4")]),
    ("reject zero target wildcards", [("target != 0 && target != field", "target != field")]),
    ("keep empty intersections", [("clipLeft >= clipRight || clipTop >= clipBottom", "false")]),
    ("use unsigned rectangle comparisons", [("if (left > clipLeft)",
                                             "if (static_cast<uint32_t>(left) > static_cast<uint32_t>(clipLeft))")]),
    ("forget window offset negation", [("0u - field(tile + 240)", "field(tile + 240)")]),
    ("select one bin bit per tile", [("3u << shift", "1u << shift")]),
    ("restore zero as a zero bin mask", [("mask != 0 ? mask : 0xFFFFFFFFu", "mask")]),
    ("refill at equality", [("field(0) > field(8)", "field(0) >= field(8)")]),
    ("ignore the returned refill cursor", [("command = static_cast<uint32_t*>(rage_A980(device));",
                                           "rage_A980(device);")]),
    ("lose one dirty register bit", [("UINT64_C(0x3800)", "UINT64_C(0x3000)")]),
]


def main():
    import argparse
    from pathlib import Path
    from liftcheck.runner import Checker, Options

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--mutations", action="store_true")
    args = ap.parse_args()
    path = Path(__file__)
    rc = Checker(path, Options(seed=args.seed)).run()
    if rc:
        return rc
    if args.mutations:
        for name, patches in MUTATIONS:
            rc = Checker(path, Options(seed=args.seed, patches=tuple(patches))).run()
            assert rc == 1, ("expected a semantic FAIL, not a build/spec error", name, rc)
            print(f"CAUGHT {name}")
        print(f"PASS {path.stem}: {len(MUTATIONS)} mutations caught (seed {args.seed})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
