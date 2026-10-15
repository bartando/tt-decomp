"""msgMsgSink::msgMsgSink (really dialogManager's constructor, 0x822EC7F8):
vtables, 32 message slots of 0x480 bytes from +0x360, zeroed header region
and two tail words. Leaf; the object is filled with random bytes first so
every store shows.

Failed until msgMsgSink (src/game/misc/pong_misc.hpp) dropped its C++
virtuals (a hidden vptr in front of the explicit `vtable` member) and got
explicit padding (+0x0B, +0x22, +0x2D, +0xE8, +0x118, +0x140 were misaligned
or missing), which put every header field and the 210-word clear 4 bytes off."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "msgMsgSink::msgMsgSink"
ADDRESS = 0x822EC7F8
SOURCE = "src/game/network/msg_msg_sink.cpp"
RET = None
EXTERNS = {"g_msgSinkTemplate": 0x8261A0C0}   # the asm: lis 0x8262; addi -0x5F40


def inputs(t):
    obj = t.alloc(0x93A0, "dialogManager")
    t.args(r3=obj)
