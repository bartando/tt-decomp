"""0x8218C690: mode gates, controlled slot and post-cast global/slot reloads."""
from liftcheck.spec import *

FUNCTION = "game_C690"
ADDRESS = 0x8218C690
SOURCE = "src/game/player/player_control_queries.cpp"
TRIALS = 1000
EXTERNS = {"g_render_obj_ptr": 0x825EAB2C, "g_pGameLogic": 0x8260639C}


def cast(ctx):
    assert ctx.r(4) == 0 and ctx.r(7) == 0
    # The cast result is discarded. Expose ordering by changing both objects
    # the caller must reload after the cast, without depending on that result.
    player = int.from_bytes(ctx.read(ctx.r(3) + 0x58, 4), "big")
    network = int.from_bytes(ctx.read(ctx.r(3) + 0x5C, 4), "big")
    slot = ctx.rng.choice([-1, 0, 1, 2])
    ctx.write(player + 0x1D0, slot.to_bytes(4, "big", signed=True))
    ctx.write(network + 0x128, ctx.rng.choice([slot, slot + 1]).to_bytes(4, "big", signed=True))
    ctx.write(0x825EAB2C, network.to_bytes(4, "big"))
    ctx.ret(r3=ctx.rng.choice([0, player, network]))


CALLS = {0x82430978: model(cast, args=("r3", "r4", "r5", "r6", "r7"))}


def inputs(t):
    player = t.alloc(0x1E0, "player")
    network = t.alloc(0x130, "network")
    replacement = t.alloc(0x130, "replacementNetwork")
    logic = t.alloc(0x60, "logic")
    t.w32(logic + 0x58, player)
    t.w32(logic + 0x5C, replacement)
    mode = [-1, 0, 1, 2, 3, 255][t.index % 6]
    slot = t.rng.choice([-1, 0, 1, 2])
    t.w32(player + 0x1D0, slot)
    t.w32(network + 0x128, t.rng.choice([slot, slot + 1]))
    t.w32(logic + 0x54, [-1, 0, 1, 2, 3][(t.index // 6) % 5])
    t.w32(t.sym("lbl_825C9A2C"), mode)
    t.w32(t.sym("g_render_obj_ptr"), network)
    t.w32(t.sym("g_pGameLogic"), logic)
    t.args(r3=player)
