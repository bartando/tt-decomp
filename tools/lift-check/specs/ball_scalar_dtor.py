"""gmBallNode::ScalarDtor (0x82280B18): vtable stores, base destructor, optional free."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmBallNode::ScalarDtor"
ADDRESS = 0x82280B18
SOURCE = "src/game/ball/pong_ball.cpp"

CALLS = {
    0x823D90A0: stub(ret="void"),   # sgPhysicalObject destructor
    0x820C00C0: stub(ret="void"),   # rage_free
}


def inputs(t):
    node = t.alloc(0x150, "node", ctype="gmBallNode")
    t.args(r3=node, r4=t.rng.choice([0, 1, 2, 3, t.u32()]))
