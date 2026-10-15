"""pongCreatureInst::FragInstDtor (0x8211D470): fragInst vtable, manager's
destroy callback (+0x36C) with the create handle, then ~phInst (0x822C8FD0)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst::FragInstDtor"
ADDRESS = 0x8211D470
SOURCE = "src/game/creature/pong_creature.cpp"

CALLS = {
    "onDestroy": stub(ret="void", args=("r3", "r4")),
    0x822C8FD0: stub(ret="void"),        # ~phInst (own spec)
}


def inputs(t):
    mgr = t.alloc(0x380, "manager")
    t.w32(mgr + 0x36C + 0x0C, t.fake_fn("onDestroy"))
    t.w32(0x826063B8, mgr)
    inst = t.alloc(0x130, "inst")
    t.args(r3=inst)
