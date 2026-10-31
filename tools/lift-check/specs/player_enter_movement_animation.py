"""0x820CE2B8: enter locomotion, then clear the current phase/timing state."""
import struct
from liftcheck.spec import *

FUNCTION = "game_E2B8"
ADDRESS = 0x820CE2B8
SOURCE = "src/game/player/player_mode_animation.cpp"
TRIALS = 1000
EXTERNS = {"g_swingInFlightFlag": 0x8260633C, "g_swingCountFlag": 0x82606340}


def start(ctx):
    state, phase, timing = struct.unpack(">III", ctx.read(ctx.r(3) + 4, 12))
    ctx.write(state + 0x88, struct.pack(">I", phase))
    ctx.write(state + 0x7C, struct.pack(">I", timing))


def reset_phase(ctx):
    state, timing = struct.unpack(">II", ctx.read(ctx.r(3) - 0x0C, 8))
    ctx.write(state + 0x7C, struct.pack(">I", timing))


CALLS = {
    "locomotion.vfn_3": model(start, args=("r3", "r4", "r5", "r6")),
    "crAnimBlenderState_Init": model(reset_phase),
}


def inputs(t):
    state = t.alloc(0xA0, "state")
    loco = t.alloc(0x10, "locomotion")
    phase = [t.alloc(0x1A0, f"phase{i}") for i in range(2)]
    timing = [t.alloc(0x90, f"timing{i}") for i in range(3)]
    t.w32(state + 0x94, loco)
    t.w32(loco, t.vtable("locomotion"))
    t.w32(loco + 4, state)
    t.w32(loco + 8, phase[1])
    t.w32(loco + 12, timing[1])
    t.w32(state + 0x88, phase[0])
    t.w32(state + 0x7C, timing[0])
    t.w32(phase[1] + 4, state)
    t.w32(phase[1] + 8, timing[2])
    for obj in phase:
        t.wf32(obj + 0x19C, t.rng.uniform(-5, 5))
    t.w8(t.sym("g_swingInFlightFlag"), 0xA5)
    t.w32(t.sym("g_swingCountFlag"), 0xDEADBEEF)
    t.args(r3=state)
