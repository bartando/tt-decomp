"""plrPlayerMgr::~plrPlayerMgr (0x82188D40) with bit 0 of r4 clear (the C++
destructor can't free): vtables 0x82039A24/0x82039AB0 at +0/+0x10, clear
0x82606430, release the 0x30-byte sub-objects at +0x44 then +0x14, restore
the base vtables and ReleaseSingleton(this)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "plrPlayerMgr::~plrPlayerMgr"
ADDRESS = 0x82188D40
SOURCE = "src/game/data/gd_data.cpp"
RET = None
EXTERNS = {"g_plrPlayerMgr_state": 0x82606430, "rage::ReleaseSingleton": 0x821A9420}

CALLS = {
    "plrPlayerMgr_ReleaseResourcePairs": stub(ret="void", args=("r3",)),
    0x821A9420: stub(ret="void", args=("r3",)),
}


def inputs(t):
    obj = t.alloc(0x74, "plrPlayerMgr")
    t.args(r3=obj, r4=t.rng.randrange(1 << 16) & ~1)
