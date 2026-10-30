"""DA58: swing-apex gate on the inner pongPlayerState, not the outer player.

Run all real predicate helpers and the recovery clip-time calculation. Exercise
null sub-states, both creature gates, signed frame counts, exact boundaries,
nonpositive speeds, NaNs and all three timing paths. Incoming f1 is unrelated:
the original replaces it with the recovery helper's return value.
"""
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import run, stub
from player_common import coin

FUNCTION = "pongPlayerState::IsSwingApexReached"
ADDRESS = 0x820CDA58
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 1200
FP_CONTRACT = "off"
CALLS = {addr: run() for addr in (0x820CD550, 0x820CD598, 0x820CD5F0,
                                  0x820CD6B8, 0x820DD238)}
CALLS.update({"primary.vfn_7": stub(ret=coin),
              "secondary.vfn_6": stub(ret=coin),
              "secondary.vfn_7": stub(ret=coin)})


def f32(x):
    return struct.unpack(">f", struct.pack(">f", x))[0]


def inputs(t):
    rng = t.rng
    state = t.alloc(0x200, "state", fill="zero")
    t.w8(state + 0x14, rng.choice([0, 0, 0, 1, 255]))
    for offset, name in ((0x8C, "primary"), (0x90, "secondary")):
        obj = t.alloc(16, name)
        t.w32(obj, t.vtable(name))
        t.w32(state + offset, obj if offset == 0x8C or rng.random() < .3 else 0)

    def value():
        return rng.choice([0.0, -0.0, -1.0, 1.0, math.nan,
                           math.inf, -math.inf, rng.uniform(-2, 2)])

    def clip(name, count_offset, count16=False):
        obj = t.alloc(0x160, name)
        speed_rec = t.alloc(16, name + "Speed")
        speed = value()
        count = rng.choice([0, -1, 1, -32768, 32767, rng.randrange(-100, 100)])
        t.w32(obj + 0x30, speed_rec)
        t.wf32(speed_rec + 12, speed)
        (t.w16 if count16 else t.w32)(obj + count_offset, count)
        fraction = 0.0 if speed <= 0 else f32(f32(count * f32(1 / 30)) / speed)
        return obj, speed_rec, fraction

    timing = t.alloc(0x90, "timing")
    sub, sub_speed, fraction = clip("swing", 0x154, True)
    t.wf32(sub + 0xA0, value())
    t.w32(state + 0x78, rng.choice([sub, sub, 0]))
    current = rng.choice([value(), fraction])
    t.wf32(timing + 0x1C, current)
    t.wf32(timing + 0x30, rng.choice([value(), current]))
    t.w32(state + 0x7C, rng.choice([timing, timing, 0]))

    anim = t.alloc(0x1B0, "anim")
    frames = t.alloc(16, "frameArray")
    index = rng.randrange(4)
    for i in range(4):
        frame, speed, apex = clip("frame" + str(i), 0x38)
        t.w32(frame + 0x10, speed)
        t.w32(frames + 4 * i, frame)
        if i == index:
            selected_frame, selected_speed = frame, speed
            t.wf32(anim + 0x60, rng.choice([value(), apex]))
    t.w32(anim + 4, frames)
    t.w32(anim + 0x194, index)
    t.wf32(anim + 0x19C, value())
    t.w16(anim + 0x5A, rng.choice([0, 1, 0xFFFF]))
    t.w32(state + 0x88, rng.choice([anim, anim, 0]))

    recovery = t.alloc(0xB0, "recovery")
    action, speed, apex = clip("followAction", 0x20)
    t.w32(action + 0x24, speed)
    t.w32(recovery + 0x24, rng.choice([action, action, 0]))
    t.w8(recovery + 0x2C, rng.choice([0, 0, 1, 255]))
    t.wf32(recovery + 0xAC, rng.choice([value(), apex]))
    t.w32(state + 0x80, rng.choice([recovery, recovery, 0]))
    # Directed paths keep rare numeric bugs from hiding behind earlier gates.
    mode = rng.randrange(5)
    if mode:
        t.w8(state + 0x14, 0)
        t.w32(state + 0x90, 0)
    if mode == 1:
        t.w32(state + 0x7C, timing)
        t.w32(state + 0x78, sub)
        t.wf32(sub + 0xA0, 1.0)
        t.wf32(sub_speed + 12, 1.0)
        count = rng.choice([-32768, -30, -1, 0, 1, 30, 32767])
        t.w16(sub + 0x154, count)
        t.wf32(timing + 0x1C, rng.choice([0.0, f32(count * f32(1 / 30))]))
        t.wf32(timing + 0x30, math.inf)
    elif mode == 2:
        t.w32(state + 0x7C, 0)
        t.w32(state + 0x88, anim)
        t.wf32(anim + 0x19C, rng.choice([0.0, -1.0, math.nan, 1.0]))
        t.w16(anim + 0x5A, 1)
        t.w32(selected_frame + 0x38, 30)
        t.wf32(selected_speed + 12, 1.0)
        t.wf32(anim + 0x60, rng.choice([0.0, 1.0, 2.0, math.nan]))
    elif mode == 3:
        t.w32(state + 0x7C, 0)
        t.w32(state + 0x88, 0)
        t.w32(state + 0x80, recovery)
        t.w8(recovery + 0x2C, rng.choice([0, 0, 1]))
        t.w32(recovery + 0x24, action)
        t.w32(action + 0x20, 15)
        t.wf32(speed + 12, 1.0)
        t.wf32(recovery + 0xAC, rng.choice([0.25, 0.5, 0.75, math.nan]))
    elif mode == 4:
        t.w32(state + 0x7C, 0)
        t.w32(state + 0x88, 0)
        t.w32(state + 0x80, 0)
    t.args(r3=state, f1=value())
