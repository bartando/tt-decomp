"""0x82287B50: launch/reuse, replay sample, full ring construction and publication.

StepSample is scripted at the physics boundary. All prediction appends run the
original AddSample/assignment; loop appends are compared to the lifted fields.
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *
from _bp_common import zero_stack_fill

FUNCTION = "ballPredict_ProcessHit"
ADDRESS = 0x82287B50
SOURCE = "src/game/ball/ball_process_hit.cpp"
TRIALS = 800
FTOL = 1e-6
FP_CONTRACT = "off"

GAME_STATE = 0x8271A2F8
INPUT = 0x825EAB28
BALL_SLOT = 0x8271A2F4


def u32(ctx, addr):
    return struct.unpack(">I", ctx.read(addr, 4))[0]


def f32(ctx, addr):
    return struct.unpack(">f", ctx.read(addr, 4))[0]


def w32(ctx, addr, value):
    ctx.write(addr, struct.pack(">I", value & 0xFFFFFFFF))


def wf(ctx, addr, value):
    ctx.write(addr, struct.pack(">f", value))


def script(ctx):
    return u32(ctx, u32(ctx, INPUT) + 0x108)


def reset(ctx):
    control = script(ctx)
    state = ctx.r(3)
    data = u32(ctx, state + 0x14)
    count, tail = u32(ctx, control + 8), u32(ctx, control + 12)
    w32(ctx, data + 0x25A0, (tail + count) % 120)
    w32(ctx, data + 0x25A4, tail)
    w32(ctx, data + 0x25A8, count)
    ctx.write(data + 0x2600, b"\0")


def step(ctx):
    control = script(ctx)
    mode, n = u32(ctx, control), u32(ctx, control + 4)
    sample = ctx.r(3)
    w32(ctx, control + 4, n + 1)
    # Some callbacks publish a different state object; it keeps the same ring.
    if n == 0 and u32(ctx, control + 16):
        w32(ctx, GAME_STATE, u32(ctx, control + 16))
    if n == 0 and u32(ctx, control + 20):
        w32(ctx, u32(ctx, BALL_SLOT), 0)

    wf(ctx, sample, f32(ctx, sample) + f32(ctx, control + 24))
    wf(ctx, sample + 4, f32(ctx, sample + 4) + f32(ctx, control + 28))
    bounced = 0
    z = (n + 1) * 0.2
    y = 0.5
    if mode == 1:                  # seven floor samples finish the prediction
        y = -0.1
    elif mode == 2:                # separated contacts on one side: three runs
        bounced = int(n % 2 == 0)
        z = 0.5
    elif mode == 3:                # alternating sides keep the run counter at 1
        bounced = int(n % 2 == 0)
        z = -0.5 if n % 4 == 0 else 0.5
    elif mode == 4:                # consecutive contacts do not start new runs
        bounced = 1
        z = 0.5
    elif mode == 5:                # floor expiry is accumulated, not consecutive
        y = -0.1 if n % 3 == 0 else 0.5
    elif mode == 6:                # exactly two runs then expiry ticks
        bounced = int(n in (0, 2))
        z = -0.5
    elif mode == 7:                # zero z resets the side run; NaN y never expires
        bounced = int(n % 2 == 0)
        z = 0.0
        y = float("nan")
    ctx.write(sample + 8, bytes([bounced, (n + 17) & 255, (n * 3 + 1) & 255]))
    wf(ctx, sample + 0x10, (n + 1) * 0.125)
    wf(ctx, sample + 0x14, y)
    wf(ctx, sample + 0x18, z)
    wf(ctx, sample + 0x1C, -3.0 + n * 0.01)
    for off in range(0x20, 0x50, 4):
        wf(ctx, sample + off, (off + n) * -0.03125)


def remove(ctx):
    # Serving can start playback during removal, suppressing the record call.
    replay = ctx.r(3) - 0x4020
    control = script(ctx)
    if u32(ctx, control + 32):
        w32(ctx, replay + 0x68CF0, 1)


def initial_velocities(ctx):
    control = script(ctx)
    ctx.write(ctx.r(4), ctx.read(control + 64, 16))
    ctx.write(ctx.r(5), ctx.read(control + 80, 16))
    ctx.ret(r3=1)


def transform(ctx):
    control = script(ctx)
    ctx.write(ctx.r(4), ctx.read(control + 96, 16))
    replacement = u32(ctx, control + 36)
    if replacement:
        w32(ctx, GAME_STATE, replacement)


CALLS = {
    "io_Input_poll_9D68": stub(ret=lambda ctx: u32(ctx, script(ctx) + 40), args=("r3",)),
    "ballPredict_CopyShot": run(),
    "RTDynamicCast": stub(ret=lambda ctx: ctx.r(3), args=("r3", "r4", "r5", "r6", "r7")),
    "nop_8240E6D0": stub(ret="void", args=("r3",)),
    "game_3860": model(reset, args=("r3", "r4", "r5")),
    "gdBallPredictData::AddSample": run(),
    "gdBallPredictSample::operator=": run(),
    "BallReplay_RemoveSample": model(remove, args=("r3", "r4")),
    "gdReplayMgr_RecordBallSample": stub(ret="void", args=("r3", "r4"), deref={"r4": 0x30}),
    "BallPredict_StepSample": model(step, args=("r3", "r4"), deref={"r3": 0x50}),
    "BallPredict_RetimeSamplesForLaunchVelocity": stub(ret="void", args=("r3", "r4"), deref={"r3": 16}),
    "BallPredict_ResetHitIds": stub(ret="void", args=("r3",)),
    "gdBallPredictData::BuildBounceList": stub(ret="void", args=("r3", "r4")),
    "BallPredict_Dump": stub(ret="void", args=("r3",)),
    "pg_70C8_g": stub(ret="void", args=()),
    "BallPredict_GetInitialVelocities": model(initial_velocities, args=("r3", "r4", "r5")),
    "pongPlayer_5010_g": model(transform, args=("r3", "r4", "r5", "r6")),
    "PostPageGroupMessageFmt": stub(ret="void", args=("r3", "r4", "r5", "r6")),
}

EXTERNS = {"gdBallPredictSample::operator=": 0x820D6E58,
           "game_3860": 0x821D3860}


def inputs(t):
    zero_stack_fill(t)
    rng = t.rng
    control = t.alloc(128, "physics script")
    input_obj = t.alloc(0x110, "input")
    t.w32(input_obj + 0x108, control)
    t.w32(INPUT, input_obj)
    t.wf32(input_obj + 0x104, rng.choice([0.2, 0.5, 1.0, 1.5, 3.0]))
    loop = t.alloc(0x210, "loop")
    t.wf32(loop + 0x208, rng.choice([30.0, 50.0, 60.0, 120.0]))
    t.w32(0x825EAB30, loop)
    clock = t.alloc(0x40, "clock")
    now = rng.choice([0.0, 2.0, 8.0, 1000.0])
    t.wf32(clock + 0x30, now)
    t.w32(0x8271A2E8, clock)
    replay = t.alloc(0x68D00, "replay")
    t.w32(replay + 0x68CF0, rng.choice([0, 0, 0, 1, 2]))
    t.w32(replay + 0xE8E8, rng.randrange(1, 900))
    t.w32(0x8271A2EC, replay)
    t.w32(0x825CB3C4, rng.choice([0, 0, 0, 1, 2]))

    def predict(name):
        data = t.alloc(0x2800, name)
        t.floats(data, 8, -3, 3)
        # Defined, diverse sample payloads; padding remains random and compared.
        for i in range(120):
            sample = data + 0x20 + i * 0x50
            t.wf32(sample, rng.choice([now, now - 1.0, rng.uniform(0, 10)]))
            t.wf32(sample + 4, rng.uniform(-5, 5))
            t.floats(sample + 0x10, 16, -3, 3)
        tail = rng.choice([0, 118, 119])
        count = rng.choice([0, 1, 2, 5, 119, 120])
        t.w32(data + 0x25A0, (tail + count) % 120)
        t.w32(data + 0x25A4, tail)
        t.w32(data + 0x25A8, count)
        return data

    data = predict("prediction")
    states = [t.alloc(0x40, "game state"), t.alloc(0x40, "replacement state")]
    for state in states:
        t.w32(state + 0x14, data)
        t.wf32(state + 0x28, rng.uniform(0, 1))
    t.w32(GAME_STATE, states[0])
    final_state = t.alloc(0x40, "transformed state")
    t.w32(final_state + 0x14, predict("transformed prediction"))

    ball = t.alloc(0xD0, "ball")
    archetype = t.alloc(0x10, "archetype")
    bound = t.alloc(0x10, "bound")
    t.w32(ball + 4, archetype)
    t.w32(archetype + 0xC, bound)
    t.wf32(bound + 8, rng.choice([0.01, 0.02, 0.5]))
    slot = t.alloc(4, "ball slot")
    t.w32(slot, ball)
    t.w32(BALL_SLOT, slot)

    hit = t.alloc(0x140, "hit")
    t.floats(hit + 0x10, 0xB8 // 4, -3, 3)
    t.wf32(hit + 0x84, rng.choice([-5.0, -1.0, -0.5, -0.0, 0.25, 1.0, 5.0, float("nan")]))
    t.wf32(hit + 0x134, rng.choice([now, now - 1.0, 0.0, rng.uniform(-2, 5)]))
    t.w16(hit + 0xC6, rng.choice([0, 0x1000, 0x1001]))
    velocity = t.alloc(16, "velocity")
    spin = t.alloc(16, "spin")
    t.floats(velocity, 4, -5, 5)
    t.floats(spin, 4, -5, 5)
    if t.index % 11 == 0:
        t.wf32(spin, 1001.0)

    t.w32(control, t.index % 8)
    t.w32(control + 4, 0)
    t.w32(control + 8, 118 if t.index % 17 == 0 else 0)
    t.w32(control + 12, rng.choice([0, 118, 119]))
    t.w32(control + 16, rng.choice([0, states[1]]))
    t.w32(control + 20, rng.choice([0, 0, 1]))
    t.wf32(control + 24, rng.choice([0.01, 0.1, 1.0]))
    t.wf32(control + 28, rng.choice([0.02, 0.2, 2.0]))
    t.w32(control + 32, rng.choice([0, 1]))
    t.w32(control + 36, rng.choice([0, final_state]))
    t.w32(control + 40, rng.choice([0, 0x100, 1, 255, 0x1000000]))
    for off in (64, 80, 96):
        t.floats(control + off, 4, -5, 5)
    if t.index % 13 == 0:
        t.wf32(control + 96, 1001.0)
    t.args(r3=hit, r4=velocity, r5=spin, r6=rng.getrandbits(32),
           r7=rng.getrandbits(32), r8=rng.choice([0, 1, 0x100, 0x101]),
           f1=rng.choice([-1.0, -0.0, 0.0, 0.5, 2.0, float("nan")]))
