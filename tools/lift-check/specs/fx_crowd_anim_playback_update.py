"""Crowd playback tick at 0x82386A20 (1068 bytes).

Checks queue wrap/pop, initial phase selection (types 1/11), deferred type-1
transitions, all three playback states, random speed/delay and RNG carry,
delay crossing zero, both evaluated frames, fade-in/out boundaries, promotion,
and finishing the loop/outro. Evaluator, phase-advance and frame-blend calls
are modeled: arguments/order and their writes are compared; their internals
are outside this lift. Phase advancement can wrap and change state as the
real helper does. Frame payloads differ so swapped outputs are observable.

Inputs are synthetic valid playback blocks with finite float32 values and
readable clip/frame pointers; the active or first queued animation must exist,
as required by the original's unconditional evaluation. Includes zero fade
widths and quiet NaNs in delay/phase/fade fields to exercise ordered branches.
No ignored memory, tolerance, invalid-pointer testing or match replay.
"""
import struct

from liftcheck.spec import *

FUNCTION = "fxCrowdAnimPlayback_Update"
ADDRESS = 0x82386A20
SOURCE = "src/graphics/fx_crowd.cpp"
TRIALS = 1000
FP_CONTRACT = "off"  # Only the RNG's explicit fmaf is fused.

ADVANCED = {}


def _evaluate(ctx):
    # Record the evaluated clip/time in each distinct output frame.
    ctx.write(ctx.r(5), struct.pack(">If", ctx.r(3), ctx.f(1)))


def _advance(ctx):
    current = bool(ctx.r(6))
    phase = ADVANCED[current]
    ctx.write(ctx.r(4), struct.pack(">f", phase))
    if current and phase == 0.0:
        state = struct.unpack(">I", ctx.read(ctx.r(3) + 32, 4))[0]
        if state == 0:
            ctx.write(ctx.r(3) + 32, struct.pack(">I", 1))


def _blend(ctx):
    ctx.write(ctx.r(3), ctx.read(ctx.r(4), 8))
    ctx.write(ctx.r(3) + 8, struct.pack(">f", ctx.f(1)))


CALLS = {
    "LocomotionStateAnim_88E0_g": model(
        _evaluate, args=("r3", "f1", "r5", "r6", "r7")),
    "LocomotionStateAnim_6E50_w": model(
        _advance, args=("r3", "r4", "r5", "r6"), deref={"r4": 4}),
    "rage::crAnimFrame_ApplyMatchingDofs": model(
        _blend, args=("r3", "r4", "r5", "r6", "r7", "f1", "r9")),
}


def inputs(t):
    rng = t.rng
    mode = rng.randrange(12)
    state = rng.randrange(3)
    current_type = rng.choice([0, 1, 2, 10, 11, 12, 0xFFFFFFFF])
    next_type = rng.choice([0, 1, 2, 11, 0xFFFFFFFF])
    current_present, next_present = True, False
    queued = rng.randrange(3)
    if mode in (0, 1, 2):
        current_present, queued = False, 1 if mode == 0 else 2
        current_type = [1, 11, 2][mode]
    elif mode in (3, 4, 5):
        next_present, queued = True, 0
    elif mode == 6:
        next_type, current_type, queued = 1, rng.choice([2, 11]), 1
    elif mode == 7:
        current_type, next_type, queued = 1, 1, 1
    elif mode == 8:
        state, queued = 2, 1  # Outro leaves the queue untouched.
    elif mode == 9:
        queued = 0
    elif mode == 10:
        next_present, queued = True, 0

    playback = t.alloc(64, "playback", ctype="fxCrowdAnimPlayback")
    read_index = rng.randrange(2)
    first_slot = (read_index + 1) % 2
    phases = [0.0, -0.0, -0.25, 0.125, 0.25, 0.5, 0.75, 0.875, 1.0, 1.25]
    nan = float("nan")
    fade_in = rng.choice([0.0, 0.125, 0.25, 0.5, 1.0])
    fade_out = rng.choice([0.0, 0.125, 0.25, 0.5, 1.0])
    next_phase = rng.choice(phases + [fade_in, 1.0 - fade_out, nan])
    if mode == 10:
        fade_in = rng.choice([nan, 0.25])
        fade_out = rng.choice([nan, 0.25])

    def animation(name, kind):
        obj = t.alloc(64, name)
        t.w32(obj + 20, kind)
        t.wf32(obj + 32, rng.choice([-1.0, 0.0, 0.125, 1.0, 3.0]))
        t.wf32(obj + 36, fade_in)
        t.wf32(obj + 40, fade_out)
        minimum = rng.uniform(-2.0, 2.0)
        maximum = minimum + rng.uniform(-1.0, 4.0)
        t.wf32(obj + 44, minimum)
        t.wf32(obj + 48, maximum)
        for i in range(3):
            clip = t.alloc(48, name + ".clip" + str(i))
            t.wf32(clip + 12, rng.choice([0.0, 0.125, 1.0, 3.25, 17.0]))
            t.w32(obj + 52 + 4 * i, clip)
        return obj

    current = animation("currentAnim", current_type)
    following = animation("nextAnim", next_type)
    t.w32(playback, current if current_present else 0)
    t.w32(playback + 4, following if next_present else 0)
    t.w8(playback + 8, rng.choice([0, 1, 2, 0x80, 0xFF]))
    t.wf32(playback + 12, rng.choice(phases))
    t.wf32(playback + 16, rng.choice(phases))
    t.wf32(playback + 20, rng.uniform(-2.0, 4.0))
    t.wf32(playback + 24, rng.uniform(-2.0, 2.0))
    delta = rng.choice([0.0, 0.015625, 0.125, 0.5])
    delay = rng.choice([-1.0, -0.0, 0.0, delta, delta / 2, delta * 2, nan])
    if mode == 3:
        delay = 0.0
    elif mode == 4:
        delay = -1.0
    elif mode == 5:
        delta, delay = 0.125, 0.0625  # Crossing must wait until next tick.
    t.wf32(playback + 28, delay)
    t.w32(playback + 32, state)
    t.w32(playback + 36 + 4 * first_slot,
          (current if not current_present else following) if queued else 0)
    t.w32(playback + 36 + 4 * read_index, following if queued == 2 else 0)
    t.w32(playback + 44, rng.randrange(2))
    t.w32(playback + 48, read_index)
    t.w32(playback + 52, queued)
    t.w32(playback + 56, t.alloc(16, "currentFrame"))
    t.w32(playback + 60, t.alloc(16, "nextFrame"))
    t.w32(0x825CA2C8, rng.getrandbits(32))
    t.w32(0x825CA2CC, rng.getrandbits(32))
    t.wf32(0x825CAEC0, delta)
    ADVANCED[True] = rng.choice(phases)
    ADVANCED[False] = next_phase
    t.args(r3=playback)
