"""sgRMDrawable::UpdateBounds (0x823D8EA8): own slot 31, then +0x54's slot 5."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "sgRMDrawable::UpdateBounds"
ADDRESS = 0x823D8EA8
SOURCE = "src/scene/sg_drawable.cpp"

CALLS = {
    "node.vfn_31": stub(),
    "phys.vfn_5": stub(ret="void", args=("r3", "r4", "r5", "r6", "r7")),
}


def inputs(t):
    node = t.alloc(0x60, "node")
    t.w32(node, t.vtable("node", slots=40))
    phys = t.alloc(0x10, "phys")
    t.w32(phys, t.vtable("phys", slots=8))
    t.w32(node + 0x54, phys if t.rng.random() < 0.8 else 0)
    t.args(r3=node)
