"""Timed gdInputSeq recognition: gates, enable changes, button ordering and callback state.

The remapper and button-edge predicate execute their original PPC on both sides.
Exercise inclusive timing bounds, NaNs/infinities, signed/empty button ranges,
held/released buttons, remapped directions, intermediate/final steps and callback
state changes. No memory or call-trace differences are ignored.
"""
import math
import struct

from liftcheck.spec import *

FUNCTION = "gdInputSeq_Update"
ADDRESS = 0x8220D418
SOURCE = "src/game/input/input_sequence.cpp"
TRIALS = 2048
FP_CONTRACT = "off"
# Older callers mislabel this predicate as the callback at 0x8225FFF8.
EXTERNS = {"CheckButtonPressed": 0x821DFFF8}


def notify(ctx):
    callback, sequence = ctx.r(3), ctx.r(4)
    state = int.from_bytes(ctx.read(callback, 4), "big")
    # Expose exactly what the callback saw, including the completion bit and
    # index before reset. The ordinary memory diff checks these snapshots.
    ctx.write(callback + 16, ctx.read(state, 16))
    ctx.write(callback + 32, ctx.read(sequence, 28))
    if ctx.read(callback + 4, 1) != b"\0":
        # A callback may touch runtime state: only time/index are reset after it.
        ctx.write(state, struct.pack(">I", 0xA5A5A5A5))
        ctx.write(state + 4, bytes(4))
        ctx.write(state + 8, struct.pack(">fI", 12.5, 55))


CALLS = {
    "pongPlayer_0270_g": run(),
    0x821DFFF8: run(),
    "sysCallback_Invoke": model(notify, args=("r3", "r4")),
}


def physical_button(button, mirrors):
    if 0x22 <= button <= 0x29:
        base, flags = 0x22, mirrors[:2]
    elif 0x2A <= button <= 0x31:
        base, flags = 0x2A, mirrors[2:]
    else:
        return button
    index = button - base
    if flags[0]:
        index = (4 - index) % 8
    if flags[1]:
        index = -index % 8
    return base + index


def inputs(t):
    rng = t.rng
    state = t.alloc(16, "sequence state", ctype="InputSequenceState")
    data = t.alloc(28, "gdInputSeq")
    steps = t.alloc(4 * 12, "steps")
    pad = t.alloc(0x320, "input")
    records = t.alloc(80 * 4, "button records")
    buttons = records + 8 * 4  # Permit negative IDs as well as both direction rings.
    callback = t.alloc(64, "completion callback")
    t.w32(callback, state)
    t.w8(callback + 4, rng.randrange(2))
    t.w32(pad + 0x31C, buttons)

    mirrors = [rng.choice((0, 0, 1, 2, 0x80, 0xFF)) for _ in range(4)]
    for i, value in enumerate(mirrors):
        t.w8(pad + 4 + i, value)

    first, last = rng.choice(((-3, 3), (0, 5), (0x20, 0x29), (0x22, 0x29),
                              (0x2A, 0x31), (4, 3), (-1, -3),
                              (0x7FFFFFFF, -0x80000000)))
    candidates = list(range(first, last + 1)) if first <= last else []
    wanted = rng.choice(candidates + [last + 1]) if candidates else 0
    others = [button for button in candidates if button != wanted]
    other = rng.choice(others) if others else None

    # Frequent canonical states, with stale completion and unrelated flag bits.
    flags = (rng.getrandbits(32) & ~15) | rng.choice((0, 1, 4, 5, 7, 7, 7, 7)) | rng.choice((0, 8))
    enabled = rng.choice((0, 1, 1, 1, 1, 2, 3, 0x80, 0xFF))
    present = rng.randrange(16) != 0
    count = rng.randint(1, 4)
    index = rng.randrange(count)
    t.w32(state, flags)
    t.w32(state + 4, data if present else 0)
    t.w32(state + 12, index)
    t.w8(data + 8, enabled)
    t.w8(data + 9, rng.randrange(256))  # Runtime flag 4, not this byte, gates evaluation.
    t.w32(data + 12, first)
    t.w32(data + 16, last)
    t.w32(data + 20, count)
    t.w32(data + 24, steps)

    # Binary fractions keep equality cases exact even after fadds rounding.
    scale = rng.choice((0.5, 1.0, 2.0, 8.0))
    earliest, latest = 0.25 * scale, 0.75 * scale
    desired = rng.choice((0.125, 0.25, 0.5, 0.75, 0.875)) * scale
    timing = rng.randrange(12)
    if timing == 0:
        desired = math.nan
    elif timing == 1:
        earliest = math.nan
    elif timing == 2:
        latest = math.nan
    elif timing == 3:
        desired = math.inf
    elif timing == 4:
        earliest = -math.inf
    elif timing == 5:
        latest = math.inf
    delta = rng.choice((0.0, 0.0625 * scale, -0.0625 * scale))
    t.wf32(state + 8, desired - delta)
    effective_index = 0 if enabled != bool(flags & 2) else index
    for i in range(4):
        # Adjacent steps must differ: always reading step zero is a plausible
        # broken lift, and identical array entries would conceal that mistake.
        selected = i == effective_index
        t.wf32(steps + 12 * i, earliest if selected else i * 0.125)
        t.wf32(steps + 12 * i + 4, latest if selected else i * 0.125 + 0.25)
        t.w32(steps + 12 * i + 8, wanted if selected else wanted + i + 1)

    pattern = rng.choice(("none", "expected", "expected", "other", "both", "held", "released"))
    pressed = set()
    if pattern in ("expected", "both"):
        pressed.add(physical_button(wanted, mirrors))
    if pattern in ("other", "both") and other is not None:
        pressed.add(physical_button(other, mirrors))
    for button in range(-8, 72):
        released = rng.randrange(256)
        now = released ^ (0x80 if button in pressed or pattern == "held" else 0)
        previous = released ^ (0x80 if pattern in ("held", "released") else 0)
        t.w8(buttons + 4 * button, (now & 0x80) | rng.randrange(128))
        t.w8(buttons + 4 * button + 1, (previous & 0x80) | rng.randrange(128))
        t.w8(buttons + 4 * button + 3, released)

    t.args(r3=state, r4=t.u32(), r5=pad, r6=callback, f1=delta)
