"""Handler identity and the event filter are distinct image tokens."""
from liftcheck.spec import *

FUNCTION = "msgEventHandler::MatchesType"
ADDRESS = 0x8225ED08
SOURCE = "src/game/network/msg_event_handler.cpp"


def inputs(t):
    values = [t.u32() for _ in range(3)]
    for address, value in zip((0x825C495C, 0x825C803C, 0x825C8038), values):
        t.w32(address, value)
    t.w32(0x825C5800, t.u32())
    t.args(r3=t.alloc(0x28, "handler"), r4=t.pick([*values, 0, t.u32()]))
