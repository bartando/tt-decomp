"""0x82101700: virtual type token and low-byte checked-cast result."""
from liftcheck.spec import *

FUNCTION = "game_1700"
ADDRESS = 0x82101700
SOURCE = "src/game/player/camera_node_cast.cpp"
TRIALS = 1000
EXTERNS = {"g_cameraNodeType": 0x825C7520}
CALLS = {"node.vfn_20": stub(ret=lambda c: c.rng.choice([0, 1, 0x100, 0x101, 0xFFFFFFFF]), args=("r3", "r4"))}


def inputs(t):
    node = t.alloc(0x40, "node")
    t.w32(node, t.vtable("node", slots=21))
    t.w32(0x825C7520, t.rng.getrandbits(32))
    t.args(r3=node)
