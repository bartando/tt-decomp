"""Replay-rate curve inputs, including every ramp and disabled-curve gate."""
import math

SOURCE = "src/game/player/player_animation_clock.cpp"
TRIALS = 500
FP_CONTRACT = "off"
EXTERNS = {"g_pReplayStateData": 0x8271A2EC, "g_sysTimeManager": 0x825CAEB8}


def edge(t):
    return t.rng.choice([-1.0, -0.0, 0.0, 0.25, 0.5, 1.0, 2.0,
                         math.nan, math.inf, -math.inf, t.rng.uniform(-2, 2)])


def replay_inputs(t):
    replay = t.alloc(0x68D50, "replay", fill="zero")
    lst = t.alloc(8, "curveList", fill="zero")
    t.w16(lst + 4, 1)
    t.w32(replay + 0x68D10, lst)
    t.w32(replay + 0x68D14, 0)
    t.wf32(replay + 0x68CEC, t.rng.choice([0.25, 1.0, 2.0, -1.0]))
    t.wf32(replay + 0x68D04, [-1.0, 0.0, 0.5, 1.0, math.nan][(t.index // 7) % 5])
    t.wf32(replay + 0x68D0C, t.rng.choice([-1.0, 0.0, 0.5, 2.0]))
    # rise=.5, decline=.5, hold=1, tail=.5 for these directed coefficients.
    for off, value in [(0x68D24, 0.5), (0x68D2C, 2.0), (0x68D30, 1.0),
                       (0x68D34, 1.0), (0x68D38, 1.0), (0x68D3C, 2.0)]:
        t.wf32(replay + off, edge(t) if t.index % 3 == 2 else value)
    elapsed = [-0.25, 0.0, 0.125, 0.1875, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0,
               2.25, 2.5, 3.0, math.nan][t.index % 14]
    t.wf32(replay + 0x68D28, elapsed)
    gate = (t.index // 14) % 8
    if gate == 1: t.w8(replay + 0x68CFE, t.rng.choice([1, 255]))
    if gate == 2: t.w32(replay + 0x68D10, 0)
    if gate == 3: t.w16(lst + 4, 0)
    if gate == 4: t.w32(replay + 0x68D14, -1)
    if gate == 5: t.wf32(replay + 0x68D24, -1.0)
    return replay
