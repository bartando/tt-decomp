"""0x821880D0: enter once, then canonicalize any active flag to one."""
from liftcheck.spec import *

FUNCTION = "GameMessageGuard_Enter"
ADDRESS = 0x821880D0
SOURCE = "src/game/game_message.cpp"
TRIALS = 1000
CALLS = {0x82585E0C: stub(ret="void", args=("r3",))}


def inputs(t):
    guard = t.alloc(8, "guard")
    t.w8(guard, t.rng.choice([0, 0, 1, 2, 0xFF]))
    t.w32(guard + 4, t.alloc(32, "lock"))
    t.args(r3=guard)
