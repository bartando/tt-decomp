"""Launch-speed easing retimes only primary sample clocks in the live ring."""
from liftcheck.spec import *
FUNCTION = "BallPredict_RetimeSamplesForLaunchVelocity"
ADDRESS = 0x82289738
SOURCE = "src/game/ball/ball_prediction_postprocess.cpp"
TRIALS = 1200
EXTERNS = {"g_game_state_ptr": 0x8271A2F8}
CALLS = {"crt_sin": run()}


def inputs(t):
    rng = t.rng
    state = t.alloc(0x20, "game state")
    data = t.alloc(0x2800, "live prediction", ctype="gdBallPredictData")
    other = t.alloc(0x2800, "other bank", fill="zero")
    t.w32(other + 0x25A8, 2)
    t.w32(state + 0x10, other)
    t.w32(state + 0x14, data)
    t.w32(0x8271A2F8, state)
    tail = rng.choice([0, 1, 118, 119, rng.randrange(120)])
    count = rng.choice([0, 1, 2, 3, 4, 16, 17, 18, 32, 119, 120])
    t.w32(data + 0x25A4, tail)
    t.w32(data + 0x25A8, count)
    pos = [rng.uniform(-2, 2) for _ in range(4)]
    now = rng.uniform(-3, 3)
    for i in range(120):
        p = data + 0x20 + ((tail + i + 1) % 120) * 0x50
        now += rng.uniform(0.001, 0.1)
        t.wf32(p, now)
        t.wf32(p + 4, rng.uniform(-3, 3))
        for lane in range(4):
            pos[lane] += rng.uniform(-0.2, 0.2)
            t.wf32(p + 0x10 + 4 * lane, pos[lane])
            t.wf32(p + 0x20 + 4 * lane, rng.uniform(-4, 4))
    velocity = t.alloc(16, "requested velocity", floats=[(0,4)])
    if t.index % 10 == 0:
        # A stationary span exercises zero-distance normalization.
        for i in range(120):
            p = data + 0x20 + ((tail + i + 1) % 120) * 0x50
            for lane in range(4): t.wf32(p + 0x10 + 4 * lane, pos[lane])
    mode = t.index % 6
    magnitude = [0.0, 0.01, 2.0, 10.0, 100.0, -10.0][mode]
    for lane in range(4):
        t.wf32(velocity + 4 * lane, magnitude * rng.uniform(0.2, 1.0))
    if t.index % 10 == 1:
        velocity = data + 0x20 + ((tail + 2) % 120) * 0x50 + 0x20
    t.args(r3=velocity, r4=rng.choice([0,1,2,-1,0x12345678]))
