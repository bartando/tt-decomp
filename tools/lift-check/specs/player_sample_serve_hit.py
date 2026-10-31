"""0x820DD978: four-lane hit position, optional ball timing and VMX flushing."""
from liftcheck.spec import *

FUNCTION = "game_D978"
ADDRESS = 0x820DD978
SOURCE = "src/game/player/player_serve_hit_point.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def inputs(t):
    rng = t.rng
    clip = t.alloc(0x30, "clip")
    hits = t.alloc(4 * 4, "hits")
    index = rng.randrange(4)
    chosen = 0
    for i in range(4):
        hit = t.alloc(0x70, f"hit{i}", floats=[(0x30, 8)])
        t.floats(hit + 0x30, 8, -10, 10)
        if t.index % 4 == 0:
            for lane in range(8):
                t.w32(hit + 0x30 + lane * 4, rng.choice([0, 0x80000000, 1, 0x80000001, 0x00800000]))
        t.w32(hits + 4 * i, hit)
        if i == index:
            chosen = hit
    t.w32(clip + 0x2C, hits)
    ballSlot = t.alloc(4, "ballSlot")
    instance = t.alloc(8, "ballInstance")
    body = t.alloc(0x10, "body")
    timing = t.alloc(0x0C, "timing")
    t.w32(ballSlot, rng.choice([0, instance]))
    t.w32(instance + 4, body)
    t.w32(body + 0x0C, timing)
    t.wf32(timing + 8, rng.choice([0.0, -0.0, 1.0, rng.uniform(-3, 3)]))
    t.w32(0x8271A2F4, ballSlot)
    t.wf32(0x825D30BC, rng.choice([0.006, 0.0, -1.0, rng.uniform(-1, 1)]))
    output = t.alloc(16, "output", floats=[(0, 4)])
    if t.index % 3 == 0:
        output = chosen + rng.choice([0x30, 0x40])
    t.args(r3=output, r4=clip, r5=index)
