"""Dirty device-state dispatch, mask extraction, call order and clearing.

Limits: packet emitters, vertex-fetch refresh and ApplyShaderState are boundary
models, not executed. Models compare every logical argument, all 64 mask bits,
cached source bytes, dirty masks and the +0x2CB0 sentinel at each call. They also
change dirty masks to exercise reloads and dependencies between groups. The
normal memory diff checks every write, with no ignored bytes or tolerance.

The emitter ABI differs: Xenon uses r3=device, r4=uint64 mask, r5=register,
r6=values; SysV PPC32 uses r3, r5:r6, r7, r8. Compare r3 normally and explicitly
decode/compare the remaining arguments in the model; no mask bits are omitted.
This checks the C++ call's logical values, not Xenon's single-register ABI.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_FlushDirtyState"
ADDRESS = 0x82363C00
SOURCE = "src/graphics/grc_gpu_resources.cpp"
TRIALS = 1600
FP_CONTRACT = "off"

_original_calls = []
_lift_index = 0
_mutate = False


def boundary(name, source_size=0):
    def check(ctx):
        global _lift_index
        device = ctx.r(3)
        logical = [name, device, ctx.read(device + 0x10, 40), ctx.read(device + 0x2CB0, 8)]
        if source_size:
            if ctx.side == "orig":
                mask, register, values = ctx.rec.gpr64[1], ctx.r(5), ctx.r(6)
            else:
                mask = (ctx.r(5) << 32) | ctx.r(6)
                register, values = ctx.r(7), ctx.r(8)
            logical.extend((mask, register, values, ctx.read(values, source_size)))
        if ctx.side == "orig":
            _original_calls.append(logical)
        else:
            assert _lift_index < len(_original_calls), f"extra call to {name}"
            expected = _original_calls[_lift_index]
            assert logical == expected, f"call #{_lift_index + 1} to {name}: logical arguments/state differ"
            _lift_index += 1

        if _mutate:
            # A callee can set/clear dirty groups, including the current group.
            # Use the same per-call random stream on each side.
            for offset in (0x10, 0x18, 0x20, 0x28, 0x30):
                if ctx.rng.randrange(3) == 0:
                    mask = ctx.rng.choice((0, ctx.rng.getrandbits(64), 1 << ctx.rng.randrange(64)))
                    ctx.write(device + offset, mask.to_bytes(8, "big"))

    return model(check, args=("r3",))


CALLS = {
    "phBoundBVH_2980_p39": boundary("refresh vertex fetch"),
    "grcDevice_ApplyShaderState": boundary("apply shaders"),
    0x82362658: boundary("registers", 256),
    0x82362718: boundary("fetch descriptors", 768),
    0x82362858: boundary("float constants", 4096),
}


def inputs(t):
    global _original_calls, _lift_index, _mutate
    _original_calls, _lift_index = [], 0
    rng = t.rng
    device = t.alloc(0x3500, "device")
    _mutate = rng.randrange(4) == 0
    mode = rng.randrange(6)
    for offset in (0x10, 0x18, 0x20, 0x28, 0x30):
        t.w64(device + offset, 0)
    if mode == 1:
        # Isolate individual bits, including unused bits that must just clear.
        t.w64(device + rng.choice((0x10, 0x18, 0x20, 0x28, 0x30)), 1 << rng.randrange(64))
    elif mode == 2:
        for offset in (0x10, 0x18, 0x20, 0x28, 0x30):
            t.w64(device + offset, 0xFFFFFFFFFFFFFFFF)
    elif mode == 3:
        # Every register-group boundary, plus the two special shader/fetch bits.
        boundaries = {
            0x10: (0, 1, 31, 32, 63),
            0x18: (0, 1, 31, 32, 63),
            0x20: (0, 13, 14, 29, 30, 31, 32, 63),
            0x28: (0, 4, 5, 25, 26, 37, 38, 42, 43, 63),
            0x30: (0, 4, 5, 8, 9, 10, 11, 17, 18, 25, 26, 63),
        }
        for offset, bits in boundaries.items():
            t.w64(device + offset, sum(1 << bit for bit in bits if rng.randrange(2)))
    elif mode >= 4:
        for offset in (0x10, 0x18, 0x20, 0x28, 0x30):
            t.w64(device + offset, rng.getrandbits(64) if rng.randrange(4) else 0)
    t.args(r3=device)
