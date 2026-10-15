"""gmBallNode::LoadProperties (0x82280B98): sgRMDrawable's fields, then 13 XML registrations."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmBallNode::LoadProperties"
ADDRESS = 0x82280B98
SOURCE = "src/game/ball/pong_ball.cpp"

CALLS = {
    0x823D8F18: stub(ret="void"),
    0x821A8F58: stub(ret="void"),   # RegisterSerializedField; names compare by content
}


def inputs(t):
    node = t.alloc(0x150, "node", ctype="gmBallNode")
    t.args(r3=node)
