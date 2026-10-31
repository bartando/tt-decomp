"""Predicted flight playback: crossing events, bank advancement, poses and impacts."""
import struct
from liftcheck.spec import *

FUNCTION = "pg_70C8_g"
ADDRESS = 0x822870C8
SOURCE = "src/game/ball/ball_playback.cpp"
TRIALS = 1000
EXTERNS = {"g_pongMatchTiming": 0x8271A2E8, "PostGameMessage": 0x8225E6E0}
SCRIPT = {}


def u32(c, p):
    return struct.unpack(">I", c.read(p, 4))[0]


def bounces(c):
    c.write(c.r(4), struct.pack(">I", SCRIPT["local"]))
    c.write(c.r(5), struct.pack(">I", SCRIPT["other"]))


def interpolate(c):
    c.write(c.r(5), c.read(SCRIPT["previous"] if c.f(1) == 1.0 else SCRIPT["current"], 0x50))


def state_sample(c):
    c.write(c.r(5), c.read(SCRIPT["current"], 0x50))


def advance(c):
    if c.r(3) == 1:
        c.write(SCRIPT["prediction"] + 0x25A8, struct.pack(">I", SCRIPT["remaining"]))


def get_velocity(c):
    c.write(c.r(4), struct.pack(">3f", *SCRIPT["velocity"]))


CALLS = {
    "gdBallPredictData::CountBouncesSoFar": model(bounces),
    "BallPredict_HasFlag9Crossing": stub(ret=lambda c: SCRIPT["flag9"]),
    "BallPredict_ShouldUsePrevious": stub(ret=lambda c: SCRIPT["use_previous"]),
    "BallPredict_InterpolateSamples": model(interpolate, args=("r3", "r5", "f1")),
    "BallPredict_InterpolateState": model(state_sample, args=("r3", "r5", "f1")),
    "BallPredict_AdvanceSamples": model(advance),
    "RTDynamicCast": stub(ret=lambda c: c.r(3)),
    "BallNode_IntegrateVisualSpin": stub(ret="void", args=("r3", "r4", "r5", "f1"), deref={"r6": 64}),
    "BallPhysics_QueueInactive": stub(ret=lambda c: c.rng.choice([0, 1])),
    "instance.vfn_4": model(get_velocity),
    "level.vfn_11": stub(ret="void", args=("r3", "r4")),
    "archetype.vfn_7": stub(ret=lambda c: c.rng.uniform(0.1, 4.0)),
    "PostGameMessage": stub(ret="void"),
    "nop_8240E6D0": stub(ret="void", args=("r3", "f1"), deref={"r4": 2}),
    "BallAudio_PreImpact": stub(ret="void", args=("r3", "r5", "r6", "r7", "f1")),
}


def inputs(t):
    rng = t.rng
    SCRIPT.clear()
    SCRIPT["local"], SCRIPT["other"] = rng.randrange(4), rng.randrange(4)
    SCRIPT["flag9"] = rng.choice([0, 1, 0x100, 0x101])
    SCRIPT["use_previous"] = rng.choice([0, 1, 0x100, 0x101])
    SCRIPT["velocity"] = [rng.uniform(-10, 10) for _ in range(3)]
    state = t.alloc(0x40, "game state")
    data = t.alloc(0x2800, "prediction")
    t.w32(state + 0x10, t.alloc(0x2800, "previous prediction"))
    t.w32(state + 0x14, data)
    t.w32(state + 0x2C, rng.randrange(4))
    t.w32(state + 0x30, rng.randrange(4))
    t.w32(0x8271A2F8, state)
    tail = rng.randrange(120)
    count = rng.choice([0, 1, 2, 3, 119, 120])
    t.w32(data + 0x25A4, tail)
    t.w32(data + 0x25A8, count)
    SCRIPT["prediction"] = data
    SCRIPT["remaining"] = rng.choice([count, count, 1, 2, 120])
    for i in range(120):
        p = data + 0x20 + 0x50 * i
        t.floats(p, 2, -1, 4)
        t.floats(p + 0x10, 16, -4, 4)
    t.wf32(data + 0x20 + 0x50 * ((tail + 1) % 120), rng.choice([0.0, 1.0, 1.5, float("nan")]))
    # Scripted samples straddle all court boundaries in both directions, with
    # equalities and unordered comparisons mixed in independently.
    values = [-4.0, -2.0, -1.0, -0.1, 0.0, 0.1, 1.0, 2.0, 4.0, float("nan")]
    for which in ("previous", "current"):
        p = t.alloc(0x50, which + " sampled state", floats=[(0, 2), (0x10, 16)])
        t.floats(p, 2, -1, 4)
        for off in range(0x10, 0x50, 4):
            t.wf32(p + off, rng.choice(values))
        SCRIPT[which] = p
    timing = t.alloc(0x40, "clock")
    t.wf32(timing + 0x30, 2.0)
    t.wf32(timing + 0x34, 1.0)
    t.w32(0x8271A2E8, timing)
    instance = t.alloc(0xD0, "ball instance", floats=[(0x10, 16), (0x60, 24)])
    t.w32(instance, t.vtable("instance", 5))
    t.floats(instance + 0x10, 16, -4, 4)
    t.floats(instance + 0x60, 24, -4, 4)
    t.w16(instance + 8, rng.randrange(65536))
    archetype = t.alloc(0x10, "archetype")
    t.w32(archetype, t.vtable("archetype", 8))
    bound = t.alloc(0x10, "bound")
    t.wf32(bound + 8, 0.02)
    t.w32(archetype + 0xC, bound)
    t.w32(instance + 4, archetype)
    t.w32(instance + 0x58, t.alloc(16, "audio"))
    slot = t.alloc(4, "published instance")
    t.w32(slot, instance)
    t.w32(0x8271A2F4, slot)
    level = t.alloc(4, "level")
    t.w32(level, t.vtable("level", 12))
    t.w32(0x826065E4, level)
    t.w32(0x825F5BD0, t.alloc(16, "simulator"))
    t.w32(0x82606570, t.alloc(0x150, "ball node"))
    table = t.alloc(0x20, "table")
    t.wf32(table + 0x14, 0.76)
    t.wf32(table + 0x18, 2.74)
    t.w32(0x8271A304, table)
    inp = t.alloc(0x4C, "input")
    t.w8(inp + 0x40, rng.choice([0, 1, 0x80]))
    for i in range(2):
        player = t.alloc(0x40, "player")
        t.wf32(player + 0x38, rng.choice([-2.0, -1.0, 1.0, 2.0]))
        t.w32(inp + 0x44 + 4 * i, player)
    t.w32(0x825EAB28, inp)
    t.args()
