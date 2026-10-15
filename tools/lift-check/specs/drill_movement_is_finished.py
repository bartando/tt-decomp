"""pongDrillMovement::IsFinished (slot 7, 0x8210DE88): *pPassed once every try is used."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillMovement::IsFinished"
ADDRESS = 0x8210DE88
SOURCE = "src/game/drill/pong_drill.cpp"


def inputs(t):
    rng = t.rng
    config = t.alloc(0x80, "config")
    drill = t.alloc(0x40, "drill")
    total = rng.randrange(-2, 12)
    t.w32(config + 0x10, total)                          # TotalNumTries
    t.w32(config + 0x14, rng.randrange(-2, 12))          # MinNumSuccesses
    t.w32(drill + 0x04, total + rng.randrange(-2, 3))    # tries started
    t.w32(drill + 0x08, rng.randrange(-2, 12))           # successes
    t.w8(drill + 0x24, rng.choice([0, 1]))               # finished
    t.w32(drill + 0x20, config)
    passed = t.alloc(4, "passed")
    t.args(r3=drill, r4=passed)
