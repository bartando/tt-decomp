"""Vibration reads live input, controller-owner and controller-index pointer slots."""
from liftcheck.spec import *

FUNCTION = "gdVibEvent::TriggerVibration"
ADDRESS = 0x8220F918
SOURCE = "src/game/data/gd_vib_event.cpp"


def player_id(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3), 4), "big"))


CALLS = {
    0x8225E408: model(player_id, args=("r3", "r4")),
    0x8220F480: stub(ret="void", args=("r3", "r4", "r5")),
}


def inputs(t):
    event = t.alloc(32, "event")
    player = t.alloc(4, "player")
    player_id = t.rng.randrange(4)
    t.w32(player, player_id)
    t.w32(event + 28, t.pick([0, t.alloc(16, "pattern")]))
    states = t.alloc(0x80, "states")
    indices = t.alloc(0x20, "controllerIndices")
    t.w32(states + (player_id + 14) * 4, t.pick([0, 1, 2, 255]))
    t.w32(indices + (player_id + 1) * 4, t.rng.randrange(4))
    t.w32(0x825EAB28, states)
    t.w32(0x8271A3A8, t.alloc(64, "controllerOwner"))
    t.w32(0x8271A31C, indices)
    t.args(r3=event, r4=player)
