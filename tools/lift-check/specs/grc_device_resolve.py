"""EDRAM resolve packets, texture addressing, clear paths and state restoration.

All memory writes and command words compare exactly. Helper calls are boundaries:
subresource layout, command rollover, state flush, clear packing, vertex allocation,
viewport/scissor setters, deferred clear and final submission. Models compare the
logical arguments where Xenon and SysV differ (stack slots and floating arguments).
The color packer also checks the actual v1 payload, including lvx alignment.
No ignored memory or floating-point tolerance. Both successful and failed vertex
allocation, helper-mutated device state, and repeated command rollovers are exercised.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_Resolve"
ADDRESS = 0x8235DD08
SOURCE = "src/graphics/grc_device.cpp"
TRIALS = 1200
FP_CONTRACT = "off"

_calls = []
_index = 0
_fail_vertices = False


def logical(ctx, value):
    global _index
    if ctx.side == "orig":
        _calls.append(value)
    else:
        assert _index < len(_calls), "extra boundary call"
        assert value == _calls[_index], f"boundary {_index} ({value[0]}): logical arguments/state differ"
        _index += 1


def u32(ctx, address):
    return int.from_bytes(ctx.read(address, 4), "big")


def put(ctx, address, value):
    ctx.write(address, (value & 0xFFFFFFFF).to_bytes(4, "big"))


def rollover(ctx):
    device = ctx.r(3)
    logical(ctx, ("rollover", device, ctx.read(device, 12)))
    cursor = ctx.alloc(0x1000)
    put(ctx, device, cursor)
    put(ctx, device + 8, cursor + ctx.rng.choice([0, 4, 16, 64, 0x800]))
    ctx.ret(r3=cursor)


def subresource(ctx):
    # r6..r10 are five out-pointers. Xenon's remaining slots are 8 bytes apart.
    sp = ctx.m.gpr(1)
    extra = (84, 92, 100) if ctx.side == "orig" else (8, 12, 16)
    outputs = [ctx.r(n) for n in range(6, 11)] + [u32(ctx, sp + off) for off in extra]
    logical(ctx, ("subresource", ctx.r(3), ctx.r(4), ctx.r(5)))
    values = [ctx.rng.choice([32, 64, 128, 512, 4096]), ctx.rng.getrandbits(32),
              ctx.rng.getrandbits(32), ctx.rng.getrandbits(32), ctx.rng.randint(1, 2048),
              ctx.rng.randint(1, 2048), ctx.rng.randint(1, 16),
              ctx.rng.choice([0x80001000, 0xA001F000, 0x8FFF0000, 0xBFFFF000])]
    for address, value in zip(outputs, values):
        put(ctx, address, value)


def depth(ctx):
    stencil = ctx.r(6) if ctx.side == "orig" else ctx.r(5)
    logical(ctx, ("depth", ctx.r(3), ctx.r(4), ctx.f(1), stencil))


def color(ctx):
    logical(ctx, ("color", ctx.r(3), ctx.r(4), tuple(ctx.m.assist.vmx.v[1])))
    put(ctx, ctx.r(5), ctx.rng.getrandbits(32))
    put(ctx, ctx.r(6), ctx.rng.getrandbits(32))


def vertices(ctx):
    logical(ctx, ("vertices", ctx.r(3), ctx.r(4), ctx.r(5)))
    ctx.ret(r3=0 if _fail_vertices else ctx.alloc(24))


def setup(ctx):
    device = ctx.r(3)
    logical(ctx, ("setup", device, ctx.r(4), ctx.read(device + 11864, 48)))
    # The helper advances the cursor and dirties state in the original too.
    cursor = ctx.r(4)
    put(ctx, cursor + 4, 0xABCD1234)
    ctx.ret(r3=cursor + 4)


def flush(ctx):
    device = ctx.r(3)
    logical(ctx, ("flush", device, ctx.read(device + 11864, 48)))
    if ctx.rng.randrange(2):
        put(ctx, device + 8, u32(ctx, device) - 4)
    # State reloads after the boundary matter, including tile-target detection.
    if ctx.rng.randrange(3) == 0:
        ctx.write(device + 10432, bytes([ctx.rng.choice([0, 16])]))


def viewport(name, size, offset):
    def apply(ctx):
        device, data = ctx.r(3), ctx.read(ctx.r(4), size)
        logical(ctx, (name, device, data))
        ctx.write(device + offset, data)
    return model(apply, args=("r3",), deref={})


def deferred(ctx):
    stencil = ctx.r(8) if ctx.side == "orig" else ctx.r(7)
    logical(ctx, ("deferred clear", ctx.r(3), ctx.r(4), ctx.read(ctx.r(5), 16),
                  ctx.read(ctx.r(6), 16), ctx.f(1), stencil))
    put(ctx, ctx.r(3) + 10396, ctx.rng.getrandbits(32))


CALLS = {
    "rage_A980": model(rollover, args=("r3",)),
    "grc_89D0": model(subresource, args=("r3", "r4", "r5")),
    "CCalMoviePlayer_D700_p39": model(depth, args=("r3", "r4", "f1")),
    "fiAsciiTokenizer_D808_fw": model(color, args=("r3", "r4")),
    "game_37B0": stub(ret="void", args=("r3", "r4", "r5", "r6", "r7")),
    "grc_3E20": model(flush, args=("r3",)),
    "grc_DBF8": model(setup, args=("r3", "r4")),
    "grc_A088": model(vertices, args=("r3", "r4", "r5")),
    "grcDevice_SetViewport": viewport("viewport", 24, 12808),
    "grc_5E08": viewport("scissor", 16, 12832),
    "grc_CFD8": model(deferred, args=("r3", "r4", "f1")),
    "rage_AD98": stub(ret="void", args=("r3",)),
}


def inputs(t):
    global _calls, _index, _fail_vertices
    _calls, _index = [], 0
    rng = t.rng
    _fail_vertices = rng.randrange(8) == 0
    device = t.alloc(0x3800, "device")
    texture = t.alloc(0x80, "destinationTexture")
    commands = t.alloc(0x1000, "commands")
    rect = t.alloc(16, "sourceRect") if rng.randrange(3) else 0
    point = t.alloc(8, "destinationPoint") if rng.randrange(3) else 0
    # Include unaligned color pointers: lvx rounds down; deferred clear doesn't.
    color = t.alloc(32, "clearColor") + rng.choice([0, 0, 4, 8, 12]) if rng.randrange(3) else 0
    target = rng.randrange(5)
    flags = target | rng.choice([0, 0x10, 0x20, 0x50, 0x70]) | rng.choice([0, 0x100, 0x200, 0x300])
    flags |= rng.choice([0, 0x2000]) | (rng.randrange(64) << 26)
    t.w32(device, commands)
    t.w32(device + 8, commands + rng.choice([-4, 0, 4, 32, 0x800]))
    t.w32(device + 10400, rng.choice([0, 0x100, t.u32()]))
    t.w8(device + 10432, rng.choice([0, 16, 0xFF]))
    t.w8(device + 10434, rng.choice([0, 32, 0x80, 0xA0, 0xFF]))
    t.w16(device + 11456, rng.choice([0, 1, 2, 3]))
    for i in range(5):
        surface = t.alloc(64, f"surface{i}")
        t.w16(surface + 48, rng.randrange(4))
        bound = 0 if i != target and rng.randrange(3) == 0 else surface
        t.w32(device + 12536 + i * 4, bound)
        t.w32(device + 12976 + i * 4, bound if rng.randrange(5) else surface ^ 4)
    t.w32(device + 12996, rng.choice([0, 1, 2, 4, 17]))
    t.w32(device + 12960, rng.choice([0, 1, 0x55, t.u32()]))
    for i in range(17):
        t.w32(device + 13240 + 16 * i, rng.choice([0, 1, 32, t.u32()]))
        t.w32(device + 13244 + 16 * i, rng.choice([0, 1, 16, t.u32()]))
    for offset in (16, 24, 32, 40, 48):
        t.w64(device + offset, rng.choice([0, 0xFFFFFFFFFFFFFFFF, rng.getrandbits(64)]))
    for i in range(8):
        t.w32(device + 11460 + 4 * i, rng.choice([0x10000, 0x110000, t.u32()]))
    t.w32(device + 11776, rng.choice([0, 1, t.u32()]))
    # Signed 15-bit scissors; force containment and expansion both often.
    scissor = rng.choice([(-100, -100, 8191, 8191), (0, 0, 8, 8), (-20, 10, 40, 60)])
    for offset, pair in ((11524, scissor[:2]), (11528, scissor[2:])):
        t.w32(device + offset, (pair[0] & 0x7FFF) | ((pair[1] & 0x7FFF) << 16))
    fmt = rng.choice([6, 22, 23, 27, 28, 29, 30, 36, 37, 38, 54, 55, 56, 57, 63, rng.randrange(64)])
    # Every entry here has a nonzero block size in the image; patch all entries
    # to vary sizes independently of the chosen numeric format, including 31.
    t.w16(0x82065C68 + fmt * 2, (rng.choice([1, 2, 4, 8, 16, 31]) << 3) | rng.randrange(8))
    t.w32(texture + 16, (t.u32() & ~0xFFC0000C) | (rng.randrange(4) << 2) | (rng.randrange(1, 512) << 22))
    t.w32(texture + 20, rng.choice([0x80001000, 0xA001F000, 0x8FFF0000, 0xBFFFF000]) | fmt | (rng.randrange(4) << 6))
    t.w32(texture + 24, t.u32())
    t.w32(texture + 28, rng.randrange(16) | rng.choice([0, 0x80000000]))
    t.w32(texture + 36, (t.u32() & ~0x600) | rng.choice([0, 0x200, 0x400, 0x600]))
    if rect:
        coords = rng.choice([(0, 0, 32, 32), (-19, -8, 39, 70), (5, 7, 20, 30), (-100, -100, -8, -1)])
        for i, value in enumerate(coords):
            t.w32(rect + 4 * i, value)
    if point:
        t.w32(point, rng.choice([0, 5, -7, t.u32()]))
        t.w32(point + 4, rng.choice([0, 3, -8, t.u32()]))
    for address in range(0x82606640, 0x82606654, 4):
        t.w32(address, rng.randrange(2))
    stencil = t.u32()
    # The same logical 10th argument in the two platform ABIs.
    t.w32(t.sp + 92, stencil)
    t.w32(t.sp + 8, stencil)
    t.args(r3=device, r4=flags, r5=rect, r6=texture, r7=point, r8=t.u32(),
           r9=rng.choice([0, 0, 1, 2, 7]), r10=color, f1=rng.uniform(0, 1))


# Run directly with PYTHONPATH=tools/lift-check to check deliberately broken copies.
# Options.patches changes only the checker's build copy, never the checked-in lift.
MUTATIONS = [
    ("drop wrapped dimension bit", "((header[7] >> 30) & 2u) + 1u", "1u"),
    ("wrong remapped format", "case 54: format = 7;", "case 54: format = 8;"),
    ("lose upper dirty-mask bit", "dirty(32) |= UINT64_C(0x8000000000000000);",
     "dirty(32) |= UINT64_C(0x4000000000000000);"),
    ("wrong rectangle alignment", "(static_cast<uint32_t>(sourceRect[2]) + 7u) & ~7u",
     "(static_cast<uint32_t>(sourceRect[2]) + 3u) & ~3u"),
    ("drop scissor restoration", "grc_5E08(device, savedScissor);", "/* omitted restoration */"),
    ("wrong pixel offset", "static_cast<float>(left) - pixelOffset", "static_cast<float>(left) + pixelOffset"),
]

if __name__ == "__main__":
    from pathlib import Path
    from liftcheck.runner import Checker, Options
    source = (Path(__file__).resolve().parents[3] / SOURCE).read_text()
    for label, before, after in MUTATIONS:
        assert source.count(before) == 1, f"mutation target is missing or ambiguous: {label}"
        print(f"MUTATION: {label}", flush=True)
        result = Checker(Path(__file__), Options(trials=200, seed=7, patches=((before, after),))).run()
        if result != 1:
            raise SystemExit(f"mutation was not caught as a divergence: {label} (exit {result})")
    print(f"PASS: caught all {len(MUTATIONS)} intentional mutations")
