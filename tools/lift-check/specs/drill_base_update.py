"""pongTrainingDrill::Update (slot 6, 0x8210D098): the optional time limit."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongTrainingDrill::Update"
ADDRESS = 0x8210D098
SOURCE = "src/game/drill/pong_drill.cpp"


def inputs(t):
    rng = t.rng
    drill = t.alloc(0x40, "drill")
    dt = rng.choice([rng.uniform(0.0, 0.1), 0.0, rng.uniform(0.5, 2.0)])
    t.wf32(drill + 0x14, rng.choice([-1.0, 0.0, dt, rng.uniform(0.0, 1.0), rng.uniform(-1.0, 3.0)]))
    t.args(r3=drill, f1=dt)
