"""pongTrainingDrill::OnRallyEnd (slot 29, 0x8210D660): a random ball speed in
[min, max] from the drills' MWC generator (`mulld` + `add`, the carry is the
upper half). Seed and carry are random, so the generator state left behind is
compared too.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongTrainingDrill::OnRallyEnd"
ADDRESS = 0x8210D660
SOURCE = "src/game/drill/pong_drill.cpp"


def inputs(t):
    rng = t.rng
    config = t.alloc(0x40, "config")
    lo = rng.choice([rng.uniform(0.5, 20.0), 0.0, -1.0])
    hi = rng.choice([lo, lo + rng.uniform(0.0, 10.0), lo - 1.0, rng.uniform(0.5, 20.0)])
    t.wf32(config + 0x18, lo)
    t.wf32(config + 0x1C, hi)
    drill = t.alloc(0x40, "drill")
    t.w32(drill + 0x20, config)
    t.w32(0x825CA2C8, rng.getrandbits(32))
    t.w32(0x825CA2CC, rng.getrandbits(32))
    event = t.alloc(0x90, "event")
    t.args(r3=drill, r4=event)
