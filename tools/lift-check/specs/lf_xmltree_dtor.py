"""xmlTree destructor body (0x821A8070, called atArray_Clear): root and entry array teardown."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "atArray_Clear"
ADDRESS = 0x821A8070
SOURCE = "src/rage/data/at_types.cpp"

CALLS = {
    0x820C2980: stub(),   # xmlTreeEntry delete[]
    "root.vfn_0": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    tree = t.alloc(0x10, "tree")
    if t.rng.random() < 0.7:
        root = t.alloc(0x10, "root")
        t.w32(root, t.vtable("root"))
        t.w32(tree + 4, root)
    else:
        t.w32(tree + 4, 0)
    t.w32(tree + 8, t.alloc(0x40, "entries") if t.rng.random() < 0.7 else 0)
    t.args(r3=tree)
