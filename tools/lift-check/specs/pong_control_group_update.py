"""Match-driven master/direct/reverb/effect fades, including skip and override paths.

The registry and two state selectors are modeled at their call boundaries; the
actual PPC approach helper runs on both sides. All state, calls (including the
promoted double in the log), and four override bytes remain observable.
"""
import math
import struct

from liftcheck.spec import *

FUNCTION = "pongControlGroup::Update"
ADDRESS = 0x821B7038
SOURCE = "src/game/match/pong_game.cpp"
TRIALS = 1200
FP_CONTRACT = "off"


def lookup(ctx):
    ctx.ret(r3=struct.unpack(">I", ctx.read(ctx.r(3), 4))[0])


def select_state(ctx):
    # Scripted selector results live beyond the real 168-byte group. Exercise
    # callee writes, priority, and rereads without retesting the two selectors.
    group = ctx.r(3)
    script = group + (168 if ctx.rec.target == 0x821B6E58 else 200)
    lane, new_type = struct.unpack(">ii", ctx.read(script, 8))
    if lane >= 0:
        ctx.write(group + 72 + lane * 24, ctx.read(script + 8, 20) + b"\x01")
    if new_type >= 0:
        ctx.write(group + 64, struct.pack(">i", new_type))


CALLS = {
    "pg_C2A0_g": model(lookup, args=("r3", "r4")),
    "pg_6E58_wrh": model(select_state, args=("r3",)),
    "game_6B90": model(select_state, args=("r3",)),
    "pongControlGroup_Approach": run(args=("r3", "f1", "f2", "f3"), deref={"r3": 4}),
    "pongControlGroup_LogMultiplier": stub(ret="void", args=("r3", "r4", "r5")),
}


def inputs(t):
    rng = t.rng
    group = t.alloc(232, "control group and selector scripts")
    player = t.alloc(48, "player")
    registry = t.alloc(32, "registry")
    input_state = t.alloc(64, "input state")
    scene = t.alloc(96, "scene")
    match = t.alloc(176, "match")
    config = t.alloc(432, "fade configuration")
    name = t.alloc(32, "group name", fill=b"match_test_group\0")
    t.w32(group + 56, name)
    t.w32(registry, player)
    t.w32(input_state + 40, rng.getrandbits(32))
    t.w32(0x825EAB28, input_state)
    t.w32(0x8271A310, registry)
    t.w32(0x82606410, scene)
    t.w32(0x8271A308, match)
    t.w32(0x8271A398, config)
    t.w32(0x825CB090, rng.choice([0, 0, 0, 1, 0x80000000]))
    # Include non-canonical true bytes: these are byte tests, not bool objects.
    flag = lambda: rng.choice([0, 0, 1, 2, 0x80, 0xff])
    t.w8(player + 32, flag())
    t.w8(scene + 83, flag())
    t.w8(match + 157, flag())
    for addr in (0x82606471, 0x82606473, 0x82606484, 0x82606486, 0x82606487):
        t.w8(addr, flag())
    t.w8(group + 165, flag())
    types = [0, 1, 7, 10, 11, 14, 2, 3, 15, -1, 0x7fffffff]
    t.w32(group + 64, rng.choice(types))
    for off in range(344, 420, 4):
        t.wf32(config + off, rng.uniform(0.01, 6))
    t.wf32(0x825CAEC0, rng.choice([0, 1 / 60, 1 / 30, 0.25, rng.uniform(0, 0.5)]))
    # Epsilon boundaries use a zero target to avoid losing the epsilon in an
    # unrelated float addition. Also test unordered comparisons and infinities.
    epsilon = 0.0010000000474974513
    for lane in range(4):
        fade = group + 72 + lane * 24
        target = rng.choice([0.0, rng.uniform(-4, 4)])
        current = rng.choice([target, target + epsilon * 0.5, target + epsilon,
                              target - epsilon * 2, target + 1, target - 1,
                              math.nan, math.inf, -math.inf])
        for off, value in [(0, rng.uniform(0.01, 4)), (4, target), (8, current),
                           (12, rng.uniform(0.01, 4)), (16, rng.uniform(-4, 4))]:
            t.wf32(fade + off, value)
        t.w8(fade + 20, flag())
    for script in (168, 200):
        # Most trials leave selectors inert so every state-specific branch can
        # run; others override any channel or change the type between selectors.
        t.w32(group + script, rng.choice([-1, -1, -1, 0, 1, 2, 3]))
        t.w32(group + script + 4, rng.choice([-1, -1, -1, *types[:6]]))
        for off in range(8, 28, 4):
            t.wf32(group + script + off, rng.uniform(0.01, 4))
    skip = rng.choice([0, 0, 0, 1, 2, 0x80, 0xff])
    # Bias toward each branch independently; unguided random booleans barely
    # ever reach the type-1 path after its skip/override/player/priority gates.
    case = rng.randrange(32)
    if case < 20:
        skip = 0
        t.w32(0x825CB090, 0)
        for script in (168, 200):
            t.w32(group + script, -1)
            t.w32(group + script + 4, -1)
        for addr in (0x82606471, 0x82606473, 0x82606484, 0x82606486):
            t.w8(addr, 0x80)
        t.w8(player + 32, 0)
        t.w8(scene + 83, 0x80)
        t.w8(match + 157, 0)
        for lane in range(4):
            t.w8(group + 92 + lane * 24, 0)
        t.w32(group + 64, [0, 7, 14, 1, 10, 11][case % 6])
        if 6 <= case < 12:
            missing_gate = [0x82606484, 0x82606471, 0x82606473,
                            0x82606486, match + 157, scene + 83][case - 6]
            t.w8(missing_gate, 1 if case == 10 else 0)
        elif case == 12:
            t.w32(group + 64, 1)
            t.w8(player + 32, 0x80)
        elif case == 13:
            t.w32(group + 64, 11)
            t.w8(group + 92, 0xff)
        elif case == 14:
            t.w32(group + 64, 2)
        elif case == 15:
            t.w32(group + 64, 11)
            t.w32(group + 168, 0)
        elif case == 16:
            t.w32(group + 64, 11)
            t.w32(group + 200, 0)
        elif case == 17:
            t.w32(group + 64, 2)
            t.w32(group + 172, 11)
        elif case == 18:
            t.w32(group + 64, 2)
            t.w32(group + 204, 0)
        elif case == 19:
            t.w32(group + 64, 11)
            t.w32(group + 204, 14)
    elif case < 29:
        # Skip state selection to isolate all four approach thresholds/logs.
        skip = 1 if case != 21 else 0
        t.w32(0x825CB090, 0x100 if case == 21 else 0)
        t.w8(group + 165, 0xff)
        for lane in range(4):
            fade = group + 72 + lane * 24
            t.w8(fade + 20, 0x80)
            t.wf32(fade + 4, 0)
            t.wf32(fade + 8, [1, -1, epsilon, -epsilon, epsilon * 0.5,
                              epsilon * 2, math.nan, math.inf, -math.inf][case - 20])
    t.args(r3=group, r4=skip)
