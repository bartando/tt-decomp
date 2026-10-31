"""0x823B8808: host state routing and the stack word payload containing -1."""
from liftcheck.spec import *

FUNCTION = "SignalReadyToServeMessage_Use"
ADDRESS = 0x823B8808
SOURCE = "src/game/message.cpp"
TRIALS = 1000
EXTERNS = {"lbl_825C9A2C": 0x825C9A2C, "g_pGameLogic": 0x8260639C}
PLAYER = 0


def post(ctx):
    assert ctx.r(5) == 1 and ctx.in_stack(ctx.r(6))
    assert ctx.read(ctx.r(6), 4) == b"\xFF" * 4


def formatted(ctx):
    # The equivalent format literal has a different linked address in the lift.
    assert ctx.read(ctx.r(5), 2) == b"i\0"


CALLS = {
    "PostGameMessage": model(post, args=("r3", "r4", "r5", "r6")),
    0x8225E480: model(formatted, args=("r3", "r4", "r6")),
    0x823B58E8: stub(ret=lambda ctx: PLAYER),
    0x82192668: stub(ret="void"),
}


def inputs(t):
    global PLAYER
    message = t.alloc(0x10, "message")
    logic = t.alloc(0x20, "gameLogic")
    PLAYER = t.alloc(0x20, "resolvedPlayer")
    mode = [-1, 0, 1, 2, 3][t.index % 5]
    state = [-1, 0, 8, 9, 23, 24, 25, 26, 27][(t.index // 5) % 9]
    t.w8(message + 8, t.rng.choice([0, 1, 2, 255]))
    t.w32(logic + 12, state)
    t.w32(t.sym("lbl_825C9A2C"), mode)
    t.w32(t.sym("g_pGameLogic"), logic)
    t.args(r3=message)
