"""gmBallNode's message handler (msgMsgSink base at +0x80, slot 1, 0x82281D10): flag71,
effectsHeld, the fxScale fade, Reset and the game state's message counters."""
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmBallNode_HandleMessage"
ADDRESS = 0x82281D10
SOURCE = "src/game/ball/pong_ball.cpp"

IDS = [1, 2, 0x23, 0x24, 0x29, 0x29, 0x29, 0x810, 0x81E, 0x81F, 0x821, 0x86B, 0x2801, 0x2802, 0x2803,
       0, 7, 0xFFFF]


def _read_ff(ctx):
    """msgMessage_ReadArgs(msg, "ff", &a, &b): the two floats from the message."""
    msg = ctx.r(3)
    ctx.write(ctx.r(5), ctx.read(msg + 4, 4))
    ctx.write(ctx.r(6), ctx.read(msg + 8, 4))


CALLS = {
    "node.vfn_35": stub(ret="void", args=("r3", "r4")),
    "node.vfn_25": stub(ret="void"),
    0x8225E998: model(_read_ff),
}


def inputs(t):
    rng = t.rng
    node = t.alloc(0x150, "node", ctype="gmBallNode")
    t.w32(node, t.vtable("node", 40))
    t.floats(node + 0x94, 5, -2, 2)
    gs = t.alloc(0x40, "gameState")
    t.w32(0x8271A2F8, gs)

    msg = t.alloc(0x10, "msg")
    t.w16(msg, rng.choice(IDS))
    t.wf32(msg + 4, rng.uniform(0, 3))
    t.w32(msg + 8, struct.unpack(">I", struct.pack(">f", rng.choice(
        [rng.uniform(-1, 3), 0.0, -0.0, float("nan"), 1.0])))[0])
    t.float_words.add(msg + 8)
    t.args(r3=node + 0x80, r4=msg)
