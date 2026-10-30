"""Caller-filled vertex allocation, dirty state and both draw packet paths.

Compare every command/fixup word, device write, return and boundary call exactly.
Models exercise flush-mutated masks/cursors, rollover return values, allocation
failure and side effects, and fixup-list growth. Vertex counts/strides include
truncation, overflow and the callers' real 3x28 and Nx36 layouts. GPU addresses
cover both sides of the physical-address adjustment. No ignored memory.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_BeginDrawPrimitiveUP"
ADDRESS = 0x82357630
SOURCE = "src/graphics/grc_device.cpp"
TRIALS = 1200

_boundaries = []
_index = 0
_fail_vertices = False
_vertex_address = 0


def u32(ctx, address):
    return int.from_bytes(ctx.read(address, 4), "big")


def put(ctx, address, value, size=4):
    ctx.write(address, (value & ((1 << (size * 8)) - 1)).to_bytes(size, "big"))


def boundary(ctx, value):
    global _index
    if ctx.side == "orig":
        _boundaries.append(value)
    else:
        assert _index < len(_boundaries), "extra boundary call"
        assert value == _boundaries[_index], f"boundary {_index}: arguments/state differ"
        _index += 1


def flush(ctx):
    device = ctx.r(3)
    boundary(ctx, ("flush", device, ctx.read(device + 40, 16),
                   u32(ctx, device + 11540), ctx.read(device + 12688, 1)))
    # Flush can consume masks and move the cursor; the caller must reload both.
    for offset in (40, 48):
        put(ctx, device + offset, ctx.rng.getrandbits(64), 8)
    put(ctx, device + 12688, ctx.rng.randrange(256), 1)
    cursor = ctx.alloc(256)
    put(ctx, device, cursor)
    put(ctx, device + 8, cursor + ctx.rng.choice([-4, 0, 4, 128]))


def rollover(ctx):
    device = ctx.r(3)
    boundary(ctx, ("rollover", device, ctx.read(device, 12),
                   ctx.read(device + 48, 8), ctx.read(device + 12688, 1)))
    cursor = ctx.alloc(256)
    # Deliberately distinct: the routine uses the returned cursor after rollover.
    put(ctx, device, cursor + 4)
    put(ctx, device + 8, cursor + 128)
    ctx.ret(r3=cursor)


def vertices(ctx):
    device = ctx.r(3)
    boundary(ctx, ("vertices", device, ctx.r(4), ctx.r(5),
                   ctx.read(device, 12), ctx.read(device + 48, 8),
                   ctx.read(device + 12688, 1)))
    # The real allocator can update device cursors even when it returns null.
    put(ctx, device, ctx.alloc(256))
    ctx.ret(r3=0 if _fail_vertices else _vertex_address)


def grow_fixups(ctx):
    fixups = ctx.r(3)
    boundary(ctx, ("grow fixups", fixups, ctx.read(fixups, 16)))
    result = ctx.alloc(32)
    put(ctx, fixups + 8, result + 4)
    put(ctx, fixups + 12, result + 32)
    ctx.ret(r3=result)


CALLS = {
    "grcDevice_FlushDirtyState": model(flush, args=("r3",)),
    "rage_A980": model(rollover, args=("r3",)),
    "grc_A088": model(vertices, args=("r3", "r4", "r5")),
    "grc_9B60": model(grow_fixups, args=("r3",)),
}


def inputs(t):
    global _boundaries, _index, _fail_vertices, _vertex_address
    _boundaries, _index = [], 0
    rng = t.rng
    device = t.alloc(0x3800, "device")
    commands = t.alloc(256, "initialCommands")
    fixups = t.alloc(64, "fixups") + rng.choice([0, 4, 16])
    _fail_vertices = rng.randrange(5) == 0
    # Returned memory is filled by the caller, so this function never dereferences it.
    _vertex_address = rng.choice([t.alloc(16, "vertices"), 0x80001000, 0xA0001000,
                                  0x8FF00000, 0x90000000, 0xBFF00000, 0xFFF00000])
    count, stride = rng.choice([(3, 28), (rng.randrange(1, 1000), 36),
                                (0, 0), (1, 1), (65535, 1020), (65536, 1024),
                                (0xFFFFFFFF, 0xFFFFFFFF), (t.u32(), t.u32())])
    t.w32(device, commands)
    t.w32(device + 8, commands + rng.choice([-4, 0, 128]))
    t.w32(device + 11540, rng.choice([0, 1, t.u32()]))
    t.w8(device + 11424, rng.choice([(stride >> 2) & 255, rng.randrange(256)]))
    t.w8(device + 12688, rng.randrange(256))
    for offset in (40, 48):
        t.w64(device + offset, rng.choice([0, 0x400, 0x80, 0xFFFFFFFFFFFFFFFF,
                                          rng.getrandbits(64)]))
    t.w8(device + 10432, (rng.randrange(256) & ~4) | rng.choice([0, 4]))
    t.w8(device + 12299, rng.choice([0, 1, 2, 63, 255]))
    t.w32(device + 13560, fixups)
    # Exact fit must avoid growth; one word short must grow.
    t.w32(device + 13564, fixups + rng.choice([0, 12, 16, 32]))
    t.args(r3=device, r4=rng.choice([0, 8, 63, 64, 0xFFFFFFFF, t.u32()]),
           r5=count, r6=stride)


# Options.patches mutates only the checker's build copy. Run this file directly
# with PYTHONPATH=tools/lift-check to prove that each independent bug is detected.
MUTATIONS = [
    ("lose upper dirty bit", "dirty(40) |= UINT64_C(0x2000000000000000);",
     "dirty(40) |= UINT64_C(0x1000000000000000);"),
    ("skip temporary fetch suppression", "dirty(48) &= ~UINT64_C(0x400);",
     "/* missing suppression */"),
    ("lose saved stride", "state[12688] = savedStride;", "state[12688] = 0;"),
    ("wrong vertex word count", "(vertexCount * vertexStride) >> 2",
     "(vertexCount * vertexStride) >> 1"),
    ("lose physical address adjustment", "physical(address(vertices)) | 3u",
     "(address(vertices) & 0x1FFFFFFFu) | 3u"),
    ("wrong draw opcode", "emit(0xC0012201); emit(drawState); emit(draw);",
     "emit(0xC0012200); emit(drawState); emit(draw);"),
    ("grow on exact fit", "word(13560) + 16u > word(13564)",
     "word(13560) + 16u >= word(13564)"),
    ("wrong fixup address", "physical(address(fixup + 1) & ~1u) | 1u",
     "physical(address(fixup) & ~1u) | 1u"),
    ("publish cursor on success", "word(13652) = address(cursor);",
     "word(0) = address(cursor); word(13652) = address(cursor);"),
    ("omit cursor restoration on failure", "word(0) = address(cursor);\n        return nullptr;",
     "return nullptr;"),
]

if __name__ == "__main__":
    from pathlib import Path
    from liftcheck.runner import Checker, Options

    source = (Path(__file__).resolve().parents[3] / SOURCE).read_text()
    # Confine mutation replacements to this function, even if neighbours use the
    # same PM4 literals. The whole replacement is unique in the translation unit.
    start = source.index('extern "C" void* grcDevice_BeginDrawPrimitiveUP(')
    end = source.index("\n// Resolve an EDRAM", start)
    original = source[start:end]
    for label, before, after in MUTATIONS:
        assert original.count(before) >= 1, f"missing mutation target: {label}"
        mutated = original.replace(before, after)
        print(f"MUTATION: {label}", flush=True)
        result = Checker(Path(__file__), Options(trials=200, seed=7,
                         patches=((original, mutated),))).run()
        if result != 1:
            raise SystemExit(f"mutation was not caught as a divergence: {label} (exit {result})")
    print(f"PASS: caught all {len(MUTATIONS)} intentional mutations")
