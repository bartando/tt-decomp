"""gmBallNode's msgMsgSink-base slot 0 (0x82282498): this -= 0x80, tail call ScalarDtor."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmBallNode_SecondaryDtorThunk"
ADDRESS = 0x82282498
SOURCE = "src/game/ball/pong_ball.cpp"

CALLS = {0x82280B18: stub(args=("r3", "r4"))}


def inputs(t):
    node = t.alloc(0x150, "node", ctype="gmBallNode")
    t.args(r3=node + 0x80, r4=t.rng.choice([0, 1, t.u32()]))
