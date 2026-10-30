"""rage_5D90: inferred pongDrawBucketLayer::Render.

Both frame buffers, disabled layers with callbacks, arbitrary sorted byte indices,
negative/zero/positive counts, one/two passes, signed light indices, null registry
results, both lookup-key sources, weight thresholds (including NaN), and pass -1
command growth/flag updates. Snapshots at every boundary check override lifetime
and publication order; models can change frame, counts, and manager pointers.

Callees are boundary models, not GPU/shader implementations. The reset model
initializes scratch bytes deterministically so uninitialized stack padding from
the real reset helper isn't compared. No memory ranges or differences ignored.
"""
import struct
from liftcheck.spec import *

FUNCTION = "pongDrawBucketLayer::Render"
ADDRESS = 0x82225D90
SOURCE = "src/game/pong_render.cpp"
TRIALS = 1200
FP_CONTRACT = "off"
FRAME, MANAGER, OVERRIDE = 0x825C4898, 0x826064F4, 0x825EB1D0
LOOP, ROOT, ACTIVE, DEVICE = 0x825EAB30, 0x8271A310, 0x82606564, 0x825EB988
CALLBACKS = 0x825C58EC
_snapshots = []
_positions = {}
_ranges = []
_effects = {}
_lighting = 0
_grown = 0


def boundary(name, action=None, args=("r3",), deref=None):
    def check(ctx):
        pos = _positions[ctx.side]
        state = (name, tuple(ctx.read(a, n) for a, n in _ranges))
        if ctx.side == "orig":
            _snapshots.append(state)
        else:
            assert pos < len(_snapshots), f"extra {name} boundary"
            assert state == _snapshots[pos], f"state before {name} differs at call {pos}"
        _positions[ctx.side] += 1
        for address, data in _effects.get(name, ()):
            ctx.write(address, data)
        if action:
            action(ctx)
    return model(check, args=args, deref=deref)


def reset(ctx):
    p = ctx.r(3)
    assert ctx.read(p + 528, 4) == b"\0\3\0\3", "scratch light counts must both be 3"
    assert ctx.r(4) == 0xFFFFFFFF, "reset mask"
    ctx.write(p, ctx.rng.randbytes(528))


def lookup(ctx):
    ctx.ret(r3=_lighting)


def grow(ctx):
    ctx.ret(r3=_grown)


CALLS = {
    "util_FFF8": boundary("callback", args=("r3", "r4")),
    "pongRender_ResetState": boundary("reset render state"),
    "pongLightState_Reset": boundary("reset lights", reset, args=("r3", "r4")),
    "pg_C2A0_g": boundary("lookup", lookup, args=("r3", "r4")),
    "pongLightState_Apply": boundary("apply lights", deref={"r3": 532}),
    "entry.vfn_0": boundary("draw", args=("r3", "r4")),
    "cmOperatorCtor_0B50_w": boundary("flush override"),
    "rage_A980": boundary("prepare command"),
    "grc_9B60": boundary("grow commands", grow),
    "rage_C660": boundary("flush device"),
}


def word(value):
    return (value & 0xFFFFFFFF).to_bytes(4, "big")


def inputs(t):
    global _snapshots, _positions, _ranges, _effects, _lighting, _grown
    _snapshots, _positions, _effects = [], {"orig": 0, "lift": 0}, {}
    rng = t.rng
    layer = t.alloc(480, "layer")
    frame = rng.randrange(2)
    t.w32(FRAME, frame)
    t.w8(layer + 468, rng.choice([0, 1, 2, 255, 255]))
    t.w32(layer + 32, rng.choice([0, 1, 3, 4, 4, 5, 0xFFFFFFFF]))
    vt = t.vtable("entry", slots=1)
    lights = t.alloc(0x1800, "per-entry lighting")
    _lighting = rng.choice([0, lights, lights])
    threshold = rng.choice([0.0, -0.0, 0.5, -1.0, 2.0])
    t.wf32(0x8202D110, threshold)
    t.wf32(0x8202D108, rng.choice([1.0, -0.0, rng.uniform(-10, 10)]))
    for i in range(4):
        bits = rng.choice([0x7FC12345, 0x7F800000, 0xFF800000,
                           int.from_bytes(struct.pack(">f", threshold), "big"),
                           int.from_bytes(struct.pack(">f", threshold - 1), "big"),
                           int.from_bytes(struct.pack(">f", threshold + 1), "big")])
        t.w32(lights + 5728 + i * 4, bits)
    for buf in range(2):
        entries = t.alloc(256 * 4, f"entries {buf}")
        t.w32(layer + 36 + buf * 8, entries)
        t.w32(layer + 52 + buf * 4, rng.choice([-3, 0, 1, 2, 5, 8]))
        indices = rng.sample(range(256), 8)
        # Use high indices too, so signed-char indexing cannot accidentally pass.
        indices[0] = rng.choice([0, 127, 128, 199, 255])
        for i, index in enumerate(indices):
            entry = t.alloc(32, f"entry {buf}:{i}")
            t.w32(entry, vt)
            t.w32(entry + 12, rng.choice([-0x80000000, -2, -1, 0, 1, 2, 3]))
            t.w32(entries + index * 4, entry)
            t.w8(layer + 68 + buf * 200 + i, index)

    managers = [t.alloc(96, f"manager {i}") for i in range(2)]
    for manager in managers:
        t.w32(manager + 84, rng.choice([0, t.alloc(32, "shader override")]))
    t.w32(MANAGER, managers[0])
    t.w32(OVERRIDE, rng.choice([0, t.alloc(32, "saved override")]))
    loop = t.alloc(592, "loop")
    root = t.alloc(48, "registry root")
    active = t.alloc(32, "active scene")
    t.w32(LOOP, loop)
    t.w32(ROOT, root)
    t.w32(ACTIVE, active)
    t.w8(loop + 576, rng.choice([0, 1, 2, 255]))
    for addr in [root + 32, active + 20]:
        t.w32(addr, rng.choice([-0x80000000, -1, 0, 1, 7, 0x7FFFFFFF]))
    # Both hooks are independent, including null and the last table entry.
    for i in range(9):
        t.w32(CALLBACKS + i * 8, rng.choice([0, t.alloc(16, f"callback {i}")]))
    t.w32(layer + 60, rng.choice([0, 1, 8, rng.randrange(9)]))
    t.w32(layer + 64, rng.choice([0, 1, 8, rng.randrange(9)]))

    device = t.alloc(13616, "device")
    commands = t.alloc(64, "command buffer")
    _grown = t.alloc(64, "grown command buffer")
    t.w32(DEVICE, device)
    t.w32(device + 13580, commands + 16)
    t.w32(device + 13584, commands + rng.choice([12, 16, 20, 24]))
    t.w8(device + 10432, rng.randrange(256))
    t.w64(device + 40, rng.getrandbits(64))
    # The frame is captured before reset; counts and the singleton are reloaded.
    if rng.randrange(2):
        _effects["reset render state"] = [(FRAME, word(1 - frame))]
    if rng.randrange(3) == 0:
        _effects["draw"] = [(layer + 52 + frame * 4, word(rng.choice([0, 1, 3, 8]))),
                            (MANAGER, word(managers[1]))]
    if rng.randrange(4) == 0:
        _effects["apply lights"] = [(MANAGER, word(managers[1]))]
    if rng.randrange(2):
        _effects["flush override"] = [(MANAGER, word(managers[1]))]
    if rng.randrange(2):
        # Preparation may move the command cursor; it is read after the call.
        _effects["prepare command"] = [(device + 13580, word(commands + 32))]
    _ranges = [(layer, 480), (FRAME, 4), (MANAGER, 4), (OVERRIDE, 4),
               (device, 13616), (commands, 64), (_grown, 64)]
    t.args(r3=layer, r4=rng.choice([-1, -1, -2, 0, 1, 4, 17, 18, 0x7FFFFFFF]))
