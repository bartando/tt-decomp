"""0x820DA6F0: empty/timed/alternate updates, clamp, freeze and first crossing."""
from liftcheck.spec import *

FUNCTION = "pcrSwingBlender_UpdatePhase"
ADDRESS = 0x820DA6F0
SOURCE = "src/game/player/player_swing_pose_helpers.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
EXTERNS = {"g_pongMatchTiming": 0x8271A2E8, "g_sysTimeManager": 0x825CAEB8}


def advance(ctx):
    assert ctx.read(ctx.r(3) + 0x8D, 1) == b"\0"
    ctx.write(ctx.r(3) + 0x1C, ctx.read(ctx.r(4) + 0x13C, 4))


def selected_clip(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3) + 0x140, 4), "big"))


CALLS = {
    0x820DA920: model(advance, args=("r3", "r4")),
    0x820DAAA0: model(advance, args=("r3", "r4")),
    0x820DBAA0: model(selected_clip, args=("r3",)),
    0x8240E6D0: stub(ret="void", args=("r3", "r4")),
    0x8225E6E0: stub(ret="void"),
}


def inputs(t):
    swing = t.alloc(0x90, "swing", floats=[(0x14, 3)])
    record = t.alloc(0x150, "record", floats=[0x120, 0x13C])
    clip = t.alloc(0x30, "clip", floats=[0x0C])
    name = t.alloc(16, "name", fill=b"swing_phase\0")
    t.w32(clip + 0x20, name)
    t.w32(record + 0x140, clip)
    present = t.index % 11 != 0
    t.w32(record + 0x10, clip if present else 0)
    t.w32(record + 0x14, t.rng.choice([0, clip]) if present else 0)
    t.w32(record + 0x18, t.rng.choice([0, clip]) if present else 0)
    t.w8(record + 0x138, t.rng.choice([0, 4, 8, 12, 255]))
    t.wf32(record + 0x120, t.rng.choice([-1, 0, 1, float("nan")]))
    phase_values = [-1, -0.0, 0, 0.5, 0.9999, 1, 1.1, float("nan")]
    t.wf32(swing + 0x18, t.rng.choice(phase_values))
    t.wf32(swing + 0x1C, t.rng.choice(phase_values))
    t.wf32(record + 0x13C, t.rng.choice(phase_values))
    t.wf32(swing + 0x14, t.rng.choice([-1, 0, 1, float("nan")]))
    t.w8(swing + 0x8C, t.rng.choice([0, 1, 255]))
    t.w8(swing + 0x8D, 255)
    t.wf32(clip + 0x0C, t.rng.choice([-1, 0, 0.01, 0.0333333, 1, 2, float("nan")]))
    clock = t.alloc(0x40, "clock", floats=[0x30])
    t.wf32(clock + 0x30, t.rng.choice([-1, 0, 1, 2, float("nan")]))
    t.w32(t.sym("g_pongMatchTiming"), clock)
    t.wf32(t.sym("g_sysTimeManager") + 8, t.rng.choice([0, 1 / 60, 1 / 30, -0.1, 2, float("nan")]))
    t.args(r3=swing, r4=record)
