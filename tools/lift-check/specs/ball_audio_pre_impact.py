"""8228AD58: every impact kind/mode, budgets/repeats, cue spelling/truncation,
cooldown wraparound/NaNs, native virtual calls and callback-driven data reloads.

The actual position/gain helpers run. Formatting varargs are observed explicitly:
NULL-ness plus full string contents, including cues discarded in special modes.
"""
import struct
from liftcheck.spec import *

FUNCTION = "BallAudio_PreImpact"
ADDRESS = 0x8228AD58
SOURCE = "src/game/ball/ball_audio_impact.cpp"
TRIALS = 2000
FP_CONTRACT = "off"
EXTERNS = {"snprintf": 0x820C0B40}
SCRIPT = [0]
VPROBE = [0]
FPROBE = [0]


def _u32(ctx, address): return struct.unpack(">I", ctx.read(address, 4))[0]
def _put(ctx, address, value): ctx.write(address, struct.pack(">I", value & 0xffffffff))
def _cstr(ctx, address):
    if address == 0: return None
    data = bytearray()
    while True:
        byte = ctx.read(address + len(data), 1)
        if byte == b"\0": return bytes(data)
        data += byte


def _poll(ctx):
    value, mode = struct.unpack(">II", ctx.read(ctx.r(3), 8))
    _put(ctx, 0x825C9A2C, mode)
    ctx.ret(r3=value)


def _registry(ctx):
    s = SCRIPT[0]
    _put(ctx, 0x825EAB28, _u32(ctx, s + 20))
    _put(ctx, 0x82606410, _u32(ctx, s + 12))
    ctx.ret(r3=_u32(ctx, s + 28))


def _format(ctx):
    s = SCRIPT[0]
    count = _u32(ctx, s + 64)
    _put(ctx, s + 64, count + 1)
    fmt = _cstr(ctx, ctx.r(5))
    n = fmt.count(b"%s")
    args = [_cstr(ctx, ctx.r(6 + i)) for i in range(n)]
    output = fmt
    snapshot = bytearray(4096)
    snapshot[0:4] = struct.pack(">I", n)
    for i, arg in enumerate(args):
        # NULL remains distinct from a literal '(null)' pointer at this boundary.
        snapshot[4 + i] = int(arg is None)
        text = b"(null)" if arg is None else arg
        assert len(text) < 1024
        snapshot[32 + i * 1024:32 + i * 1024 + len(text) + 1] = text + b"\0"
        output = output.replace(b"%s", text, 1)
    bound = ctx.r(4)
    rendered = output[:max(0, bound - 1)] + (b"\0" if bound else b"")
    snapshot[3200:3200 + len(rendered)] = rendered
    ctx.write(FPROBE[0] + count * 4096, snapshot)
    ctx.write(ctx.r(3), rendered)
    ctx.ret(r3=ctx.r(3))  # original returns the buffer; native return is ignored


def _event(ctx, opcode):
    s = SCRIPT[0]
    count = _u32(ctx, s + 60)
    _put(ctx, s + 60, count + 1)
    audio = _u32(ctx, s)
    emitter = ctx.r(3)
    record = struct.pack(">II", opcode, emitter)
    record += ctx.read(emitter + 0x14, 4)
    record += ctx.read(emitter + 0x20, 4) + ctx.read(emitter + 0x30, 4)
    record += ctx.read(audio + 0x320, 0x18)
    record += ctx.read(0x8271A398, 4)
    ctx.write(VPROBE[0] + count * 64, record.ljust(64, b"\0"))
    return s, audio, count


def _select(ctx):
    s, audio, ordinal = _event(ctx, 9)
    mode = _u32(ctx, s + 56)
    if mode & 1: ctx.write(0x8271A398, ctx.read(s + 8, 4))
    if mode & 2:
        _put(ctx, 0x825CAEB8 + 0x28, _u32(ctx, s + 48) + ordinal)
        ctx.write(0x825CAEB8 + 0x54, ctx.read(s + 92, 4))
        ctx.write(0x825C2EA0, ctx.read(s + 100, 4))
    if mode & 8:
        ctx.write(audio + 0x32C, ctx.read(s + 52, 4))
        ctx.write(audio + 0x328, ctx.read(s + 88, 4))
    if mode & 32: ctx.write(audio + 0x31C, ctx.read(s + 80, 4))
    if mode & 64: ctx.write(0x825C5EC8 + 8, bytes([_u32(ctx, s + 84) & 0xff]))
    field = 32 if ctx.r(3) == audio + 0x10 else 36
    ctx.ret(r3=_u32(ctx, s + field))


def _playing(ctx):
    s, audio, ordinal = _event(ctx, 19)
    if _u32(ctx, s + 56) & 4:
        for global_address, offset in ((0x82606410, 16), (0x825EAB28, 24),
                                       (0x8271A304, 68), (0x8271A2F4, 72)):
            ctx.write(global_address, ctx.read(s + offset, 4))
        ctx.write(0x825C8080, ctx.read(s + 104, 4))
    ctx.ret(r3=_u32(ctx, s + 40))


def _play(ctx):
    s, audio, ordinal = _event(ctx, 3)
    if _u32(ctx, s + 56) & 16:
        _put(ctx, ctx.r(3) + 0x14, _u32(ctx, ctx.r(3) + 0x14) ^ 0x1000)
    ctx.ret()


def _stop(ctx):
    _event(ctx, 4)
    ctx.ret()


def _envelope(ctx):
    s = SCRIPT[0]
    if _u32(ctx, s + 56) & 128:
        ctx.write(_u32(ctx, s) + 0x10 + 0x20, ctx.read(s + 96, 4))
    ctx.ret(r3=_u32(ctx, s + 44))


CALLS = {
    "BallShot_IsLocalPlay": run(),
    "io_Input_poll_9D68": model(_poll),
    "pg_C2A0_g": model(_registry),
    "BallAudio_SetEmitterPosition": run(deref={"r4": 16}),
    "BallAudio_SetEmitterGain": run(),
    "snprintf": model(_format, args=("r3", "r4", "r5")),
    "primary.vfn_9": model(_select),
    "loop.vfn_9": model(_select),
    "primary.vfn_3": model(_play),
    "loop.vfn_3": model(_play),
    "loop.vfn_4": model(_stop),
    "loop.vfn_19": model(_playing),
    "AudioControl_IsWithinActiveEnvelope": model(_envelope),
    "nop_8240E6D0": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    # Keep the empty-function mutation executable even when its optimized
    # DWARF drops the now-unused ImpactAudio type.
    audio = t.alloc(0x340, "ball audio", floats=[(0x2F4, 3)])
    position = t.alloc(16, "position", floats=[(0, 4)])
    for lane in range(4): t.wf32(position + lane * 4, rng.uniform(-2, 2))
    t.wf32(position + 4, rng.choice([.5, .64, .76, .78, 1, float("nan")]))
    for offset, name in ((0x10, "primary"), (0x1A0, "loop"), (0x240, "third")):
        emitter = audio + offset
        t.w32(emitter, t.vtable(name, 20))
        t.w32(emitter + 0x14, rng.getrandbits(32))
        t.wf32(emitter + 0x20, rng.choice([0, .25, .497, .5, 1, float("nan")]))
        t.wf32(emitter + 0x30, rng.uniform(0, 2))
        t.floats(emitter + 0x50, 8, -2, 2)
    for offset, value in ((0x2F4, 10000), (0x2F8, 5000), (0x2FC, 1000)):
        t.wf32(audio + offset, rng.choice([value, 0, -value, float("nan")]))
    t.w32(audio + 0x318, rng.choice([0, 1, 7, 15, 16, 17]))
    t.w32(audio + 0x320, rng.choice([0, 1, 2, 5, 0xffffffff]))
    t.w8(audio + 0x324, rng.choice([0, 0, 0, 1, 0x80]))
    t.w32(audio + 0x328, rng.choice([0, 1, 2, 5, 0xffffffff]))
    stamp = rng.choice([0, 1, 2, 100, 0x7fffffff, 0xfffffffe, 0xffffffff])
    t.w32(0x825CAEB8 + 0x28, stamp)
    t.wf32(0x825CAEB8 + 0x54, rng.choice([1 / 60, .5, 1, 0, -.5, float("nan")]))
    t.wf32(0x825C2EA0, rng.choice([0, 1, 3, 5, float("nan")]))
    t.wf32(0x825C8080, rng.choice([0, .25, .5, 1, float("nan")]))
    for offset in (0x32C, 0x330, 0x334):
        delta = rng.choice([0, 1, 2, 3, 59, 60, 119, 120, 121, 179, 180, 181, 0x80000000, 0xffffffff])
        t.w32(audio + offset, (stamp - delta) & 0xffffffff)
    t.w8(0x825C5EC8 + 0x30, rng.choice([0, 1, 0x80]))
    t.w8(0x825C5EC8 + 8, rng.choice([0, 0, 1, 0x80]))
    input_objects, contexts, tables, slots, configs = [], [], [], [], []
    for i in range(2):
        inp = t.alloc(0x160, f"input {i}")
        t.w32(inp, rng.choice([0, 1, 0x100, 0x101]))
        t.w32(inp + 4, rng.choice([0, 0, 1, 0xffffffff]))
        t.w32(inp + 0x14, rng.choice([0, 1, 2, 0xffffffff]))
        t.w32(inp + 0x28, rng.getrandbits(32))
        input_objects.append(inp)
        context = t.alloc(0x340, f"context {i}")
        t.w8(context + 0x58, rng.choice([0, 0, 1]))
        t.w32(context + 0xB4, rng.choice([0, inp]))
        environment = (f"ROOM{i}" if rng.randrange(3) else "E" * 190).encode() + b"\0"
        t.put(context + 0x240, environment)
        contexts.append(context)
        table = t.alloc(0x20, f"table {i}", floats=[0x14])
        t.wf32(table + 0x14, .76 if i == 0 else rng.choice([.4, .9, float("nan")]))
        tables.append(table)
        bound = t.alloc(12, f"bound {i}", floats=[8])
        arch = t.alloc(0x10, f"arch {i}")
        ball = t.alloc(8, f"ball {i}")
        slot = t.alloc(4, f"slot {i}")
        t.wf32(bound + 8, rng.choice([.02, .2]))
        t.w32(arch + 12, bound)
        t.w32(ball + 4, arch)
        t.w32(slot, rng.choice([0, ball, ball]))
        slots.append(slot)
        config = t.alloc(0x1E0, f"config {i}", floats=[(0x90, 6)])
        t.floats(config + 0x90, 6, 0, 2)
        t.w32(config + 0x1D4, rng.choice([0, 1, 3, 0xffffffff]))
        t.w32(config + 0x1D8, rng.choice([0, 1, 3, 0xffffffff]))
        configs.append(config)
    names = []
    for i in range(2):
        storage = t.alloc(20 * 4, f"name array {i}")
        names.append(storage + 4)
        for n in range(-1, 19):
            data = (f"SURFACE{i}_{n}" if rng.randrange(7) else "N" * 95).encode() + b"\0"
            t.w32(storage + (n + 1) * 4, t.alloc(len(data), f"name {i}:{n}", fill=data))
    t.w32(audio + 0x31C, names[0])
    prefix_text = ("ARENA" if rng.randrange(3) else "P" * 120).encode() + b"\0"
    prefix = t.alloc(len(prefix_text), "prefix", fill=prefix_text)
    record = t.alloc(0x30, "prefix record")
    t.w32(record + 0x28, prefix)
    registry = t.alloc(16, "registry")
    t.w32(0x8271A310, registry)
    for address, value in ((0x825EAB28, input_objects[0]), (0x82606410, contexts[0]),
                           (0x8271A304, tables[0]), (0x8271A2F4, slots[0]),
                           (0x8271A398, configs[0]), (0x82606424, registry)):
        t.w32(address, value)
    for lane in range(4): t.w32(0x82619BE0 + lane * 4, 0xffffffff if lane < 3 else 0)
    script = t.alloc(128, "callback script", fill="zero", floats=[92, 96, 100, 104])
    SCRIPT[0] = script
    values = {0: audio, 4: configs[0], 8: configs[1], 12: contexts[1], 16: contexts[0],
              20: input_objects[1], 24: input_objects[0], 28: record,
              32: rng.choice([0, 1, 0x100, 0x101, 0xff]),
              36: rng.choice([0, 1, 0x100, 0x101, 0xff]),
              40: rng.choice([0, 1, 0x100, 0x101]), 44: rng.randrange(2),
              48: rng.choice([0, 1, 2, 100, 0xffffffff]), 52: rng.getrandbits(32),
              56: rng.getrandbits(8), 60: 0, 64: 0, 68: tables[1], 72: slots[1],
              80: names[1], 84: rng.randrange(2), 88: rng.getrandbits(32)}
    for offset, value in values.items(): t.w32(script + offset, value)
    t.wf32(script + 92, rng.choice([1 / 60, .5, 0, float("nan")]))
    t.wf32(script + 96, rng.choice([.25, .5, 1]))
    t.wf32(script + 100, rng.choice([0, 1, 3, 5, float("nan")]))
    t.wf32(script + 104, rng.choice([0, .25, .5, 1, float("nan")]))
    VPROBE[0] = t.alloc(8 * 64, "virtual-call probe", fill="zero")
    for n in range(8):
        for offset in (12, 16): t.wf32(VPROBE[0] + n * 64 + offset, 0)
    FPROBE[0] = t.alloc(4 * 4096, "format argument probe", fill="zero")
    kind = [2, 3, 4, 5, 0, 1, 6, -1][t.index % 8]
    index = rng.choice([-1, 0, 7, 15, 16])
    energy = rng.choice([0, .05, .1, .5, 1, 2, -1, float("nan"), float("inf")])
    profile = t.index % 128
    # Deterministic profiles guarantee rare combinations in every seed, while
    # the other trials independently vary the callback/state combinations.
    if profile in (0, 1, 2, 3, 10, 11, 18, 19, 26, 27, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76):
        kind, index, energy = 2, 0, 2
        for off, value in ((0x318, 20), (0x320, 0), (0x328, 0), (0x32C, 0), (0x330, 0), (0x334, 0)):
            t.w32(audio + off, value)
        t.w8(audio + 0x324, 0)
        for off, value in ((0x2F4, 10000), (0x2F8, 5000), (0x2FC, 1000)): t.wf32(audio + off, value)
        t.wf32(position + 4, .5)
        t.w8(0x825C5EC8 + 8, 0)
        t.w8(0x825C5EC8 + 0x30, 0)
        t.w32(0x825CAEB8 + 0x28, 100)
        t.wf32(0x825CAEB8 + 0x54, 1)
        for config in configs:
            t.w32(config + 0x1D4, 100)
            t.w32(config + 0x1D8, 100)
        for context in contexts: t.w8(context + 0x58, 0)
        for inp in input_objects: t.w32(inp + 0x14, 1)
        for off, value in ((32, 1), (36, 1), (40, 0), (44, 0), (48, 100), (56, 0)):
            t.w32(script + off, value)
        if profile == 0:
            t.w32(script + 56, 9)  # table volume and hit counter reload after Select
            t.w32(script + 88, 37)
        if profile in (1, 2):
            kind = 3 if profile == 1 else 4
            t.w32(script + 56, 2)
            t.wf32(script + 92, float("nan"))
        if profile == 3:
            kind, index, energy = 5, 7, .5
            t.w32(script + 56, 5)
            t.wf32(tables[1] + 0x14, .76)
            t.w32(contexts[0] + 0xB4, 0)  # explicit NULL environment boundary
        if profile in (11, 19, 27):
            kind, index = 5, (15 if profile == 19 else 0)
            if profile != 19:
                for config in configs: t.w32(config + 0x1D8, 0)
            if profile == 11: t.w32(script + 56, 32)  # names change in loop Select
            else: t.w8(0x825C5EC8 + 8, 1)
        if profile == 10:
            t.wf32(position + 4, 1)
            t.w32(audio + 0x328, 5)
            for config in configs: t.w32(config + 0x1D4, 0)
        if profile == 18: t.w32(0x825CAEB8 + 0x28, 1)
        if profile == 26:
            t.w32(audio + 0x32C, 100)
            t.w32(audio + 0x320, 0xffffffff)
        if profile == 66:
            kind = 4
            t.w32(script + 56, 2)
            t.w32(script + 48, 2)
            t.wf32(script + 92, 1)
            t.wf32(script + 100, 1)
            t.wf32(0x825C2EA0, 3)
        if profile == 67:
            kind, index = 5, 7
            t.w32(script + 56, 4)
            t.wf32(tables[1] + 0x14, .76)
            t.wf32(0x825C8080, .25)
            t.wf32(script + 104, 1)
        if profile == 68:
            kind, index = 5, 7
            for inp in input_objects: t.w32(inp + 0x14, 0)
            t.wf32(0x825C8080, .25)
        if profile in (69, 74):
            t.wf32(position + 4, 1)
            for config in configs: t.w32(config + 0x1D4, 0)
            if profile == 69:
                t.w32(audio + 0x328, 5)
                t.w8(0x825C5EC8 + 8, 1)
        if profile in (70, 71):
            kind = 5
            if profile == 70:
                for config in configs: t.w32(config + 0x1D8, 0)
                t.w32(script + 36, 0x100)
            else: t.w32(script + 40, 0x100)
        if profile == 72: t.w32(script + 32, 0x100)
        if profile in (73, 75):
            kind = 3
            if profile == 73: t.w8(0x825C5EC8 + 8, 1)
            else: t.w32(audio + 0x330, 0x80000064)
        if profile == 76: t.w32(audio + 0x32C, 98)
    t.args(r3=audio, r4=rng.getrandbits(32), r5=kind, r6=position, r7=index, f1=energy)
