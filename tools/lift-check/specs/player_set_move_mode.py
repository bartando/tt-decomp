"""0x82195C00: movement-mode changes, swing cancellation, and action reset."""
from liftcheck.spec import *

FUNCTION = "pongPlayer_5C00_g"
ADDRESS = 0x82195C00
SOURCE = "src/game/player/player_move_mode.cpp"
TRIALS = 1000
EXTERNS = {"g_rendererState": 0x8260641C, "g_input_obj_ptr": 0x825EAB28}

CALLS = {
    "pongPlayer_7C78_g": stub(ret="void"),
    "pongPlayer_CheckServeInput": stub(ret=lambda ctx: ctx.rng.randrange(2)),
    "pg_6CF8": stub(ret="void"),
    "pongPlayer_BBE0_g": stub(ret="void"),
}


def inputs(t):
    player = t.alloc(0x1A00, "player")
    creature = t.alloc(0xD0, "creature")
    action = t.alloc(0x500, "action")
    settings = t.alloc(0x100, "settings")
    renderer = t.alloc(0x40, "renderer")
    slots = t.alloc(0x300, "slots")
    t.w32(t.sym("g_input_obj_ptr"), settings)
    t.w32(t.sym("g_rendererState"), renderer)
    t.w32(renderer + 0x30, slots)
    t.w32(player + 0x1C4, creature)
    t.w32(player + 0x1F0, action)
    slot = t.index % 2
    t.w32(player + 0x1D0, slot)
    modes = [0, 1, 2, 3, 4, 7, 5, 6, -1, 0x7FFFFFFF, -0x80000000]
    mode = modes[t.index % len(modes)]
    t.w32(player + 0x1CC, t.rng.choice([mode, t.rng.choice(modes)]))
    t.w8(player + 0x18B8, t.rng.choice([0, 0, 1, 0x80, 0xFF]))
    t.w8(creature + 0xC5, t.rng.choice([0, 0, 1, 0x80, 0xFF]))
    t.w32(settings + (slot + 14) * 4, t.rng.choice([0, 0, 1, 2, -1]))
    t.wf32(action + 0x4E4, t.rng.uniform(-10, 10))
    t.wf32(action + 0x4E8, t.rng.uniform(-10, 10))
    t.args(r3=player, r4=mode)
