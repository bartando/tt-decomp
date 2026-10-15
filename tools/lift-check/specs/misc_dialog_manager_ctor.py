"""msgMsgSink::msgMsgSink (really dialogManager's constructor, 0x822EC7F8):
vtables, 32 message slots of 0x480 bytes from +0x360, zeroed header region
and two tail words. Leaf; the object is filled with random bytes first so
every store shows.

Fails as of 2026-10-15: msgMsgSink (src/game/misc/pong_misc.hpp) declares ~85
C++ virtuals on top of its explicit `vtable` member, so the compiler's vptr
sits at +0 and vtable/m_subVtable/m_controlByte/+0x0C/+0x14 and the zeroed
block land 4 bytes high, while the slot array still starts at +0x360 (the
header's padding is 4 bytes short somewhere in between). The lift stores its
own vptr at +0, never zeroes +0x18/+0x1C, and its 210-word clear runs to
+0x367, wiping slot 0's initial float."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "msgMsgSink::msgMsgSink"
ADDRESS = 0x822EC7F8
SOURCE = "src/game/network/msg_msg_sink.cpp"
RET = None
EXTERNS = {"g_msgSinkTemplate": 0x8261A0C0}   # the asm: lis 0x8262; addi -0x5F40


def inputs(t):
    obj = t.alloc(0x93A0, "dialogManager")
    t.args(r3=obj)
