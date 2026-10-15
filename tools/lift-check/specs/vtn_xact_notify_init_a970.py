"""msgMsgSink_A970_2h (0x8244A970): XACT notification-object init. Stores
vtables at +0/+0xC, self-links +4/+8, keeps bit 0x20 of +0x18, stores r4..r7,
then calls slot 0 of the object at r5+4 with this+0xC (no null check) and
returns this."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "msgMsgSink_A970_2h"
ADDRESS = 0x8244A970
SOURCE = "src/game/network/pong_network_io.cpp"

CALLS = {"owner.vfn_0": stub(ret="void", args=("r3", "r4"))}


def inputs(t):
    obj = t.alloc(0x48, "notify")
    bucket = t.alloc(0x10, "bucket")
    t.w32(bucket + 4, t.vtable("owner", 4))
    t.args(r3=obj, r4=t.rng.randrange(1 << 32), r5=bucket,
           r6=t.rng.randrange(0x10000), r7=t.rng.randrange(1 << 32))
