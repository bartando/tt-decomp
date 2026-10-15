"""rage::hsmState_AttachChild (0x823EF850): copies the parent's context into the child,
runs the child's slot 5, then links the child to the parent."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::hsmState_AttachChild"
ADDRESS = 0x823EF850
SOURCE = "src/rage/core/hsm.cpp"

CALLS = {
    "child.vfn_5": stub(ret="void"),
}


def inputs(t):
    parent = t.alloc(0x20, "parent")
    child = t.alloc(0x20, "child")
    t.w32(parent, t.vtable("parent"))
    t.w32(child, t.vtable("child"))
    t.args(r3=parent, r4=child)
