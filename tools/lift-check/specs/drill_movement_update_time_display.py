"""pongDrillMovement::UpdateTimeDisplay (0x8210E378): "m:ss" clock into the HUD, and
"time_low" once the clock reaches UrgentTime.

ceil and strncpy run the game's own code on both sides; _snprintf is modelled
(it only ever sees "%d:0%d" / "%d:%d"), so the text the HUD gets is compared.
"""
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillMovement::UpdateTimeDisplay"
ADDRESS = 0x8210E378
SOURCE = "src/game/drill/pong_drill.cpp"

EXTERNS = {"ceilf": 0x824321F0, "ceil": 0x824321F0}


def _snprintf(ctx):
    def cstr(addr):
        out = b""
        while (c := ctx.read(addr + len(out), 1)) != b"\0":
            out += c
        return out.decode()
    fmt = cstr(ctx.r(5))
    vals = [struct.unpack(">i", struct.pack(">I", ctx.r(r)))[0] for r in (6, 7)]
    text = (fmt.replace("%d", "{}").format(*vals)).encode()[: ctx.r(4) - 1] + b"\0"
    ctx.write(ctx.r(3), text)
    ctx.ret(r3=len(text) - 1)


CALLS = {
    0x824321F0: run(),          # ceil
    "strncpy": run(),
    "_snprintf": model(_snprintf),
}


def inputs(t):
    rng = t.rng
    hud = t.alloc(0xC0, "hud")
    t.w32(0x82606614, hud)                                   # the training HUD
    data = t.alloc(0x80, "movementData")
    t.wf32(data + 0x74, rng.uniform(0.0, 20.0))              # UrgentTime
    drill = t.alloc(0x40, "drill")
    t.w32(drill + 0x38, data)
    t.wf32(drill + 0x28, rng.choice([rng.uniform(-3.0, 200.0), float(rng.randrange(0, 130)),
                                     rng.randrange(0, 600) + 0.5, -0.5, 0.0]))
    t.w8(drill + 0x34, rng.choice([0, 1]))                  # time_low already raised
    t.args(r3=drill)
