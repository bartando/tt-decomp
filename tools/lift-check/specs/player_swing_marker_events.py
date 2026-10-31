"""0x820DADC0: suppression, completion, signed markers and recipient mask."""
from liftcheck.spec import *

FUNCTION = "game_ADC0"
ADDRESS = 0x820DADC0
SOURCE = "src/game/player/player_swing_pose_helpers.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
EXTERNS = {"g_swingInFlightFlag": 0x8260633C}


def selected_clip(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3) + 0x13C, 4), "big"))


CALLS = {
    0x820DBAA0: model(selected_clip, args=("r3",)),
    0x8225E6E0: stub(ret="void"),
    0x820CF420: stub(ret="void"),
}


def inputs(t):
    swing = t.alloc(0x90, "swing", floats=[(0x18, 2), 0x30])
    record = t.alloc(0x140, "record", floats=[0x80])
    clip = t.alloc(0x20, "animation", floats=[0x0C])
    selected = t.alloc(0x30, "selectedClip")
    name = t.alloc(16, "name", fill=b"swing_clip\0")
    owner = t.alloc(0xD0, "owner")
    system = t.alloc(0x10, "animationSystem")
    t.w32(swing + 8, owner)
    t.w32(owner + 0xC0, system)
    t.w32(selected + 0x20, name)
    t.w32(record + 0x10, clip)
    t.w32(record + 0x13C, t.rng.choice([0, selected]))
    t.w8(t.sym("g_swingInFlightFlag"), t.index % 9 == 0)
    t.w32(swing + 0x88, t.rng.choice([0, 1, 2, 7, 8, 31, 32, 63, 64, 255, -1]))
    previous = t.rng.choice([-1, 0, 0.25, 0.5, 1, float("nan"), t.rng.uniform(-1, 2)])
    current = t.rng.choice([previous, 0, 0.25, 0.5, 1, 2, float("nan"), t.rng.uniform(-1, 2)])
    t.wf32(swing + 0x18, previous)
    t.wf32(swing + 0x1C, current)
    t.wf32(swing + 0x30, t.rng.choice([0.5, 1, 2, float("nan")]))
    t.wf32(record + 0x80, t.rng.choice([0, 1, -1, float("nan")]))
    t.wf32(clip + 0x0C, t.rng.choice([0, -1, 1, 2, float("nan")]))
    t.w16(record + 0x130, t.rng.choice([-32768, -1, 0, 15, 30, 32767]))
    t.w16(record + 0x132, t.rng.choice([-32768, -1, 0, 15, 30, 32767]))
    t.args(r3=swing, r4=record)
