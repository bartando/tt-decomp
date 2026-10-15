"""pongDrillMovement::Start (slot 4, 0x8210DBA0): base start, clock on the HUD, reticle
off, target free to leave the table."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillMovement::Start"
ADDRESS = 0x8210DBA0
SOURCE = "src/game/drill/pong_drill.cpp"


def inputs(t):
    rng = t.rng
    t.w32(0x82606614, t.alloc(0xC0, "hud"))
    target = t.alloc(0x80, "practiceTarget")
    t.w32(0x826063A8, target)

    state = t.alloc(0x90, "gameState")
    active = rng.randrange(0, 4)
    t.w32(state + 0x84, active)
    player = t.alloc(0x1850, "player")
    t.w32(state + 0x74 + 4 * active, player)
    reticle = t.alloc(0x20, "reticle") if rng.random() < 0.7 else 0
    t.w32(player + 0x1840, reticle)
    t.w32(0x82606430, state)

    drill = t.alloc(0x40, "drill")
    t.w32(drill, t.vtable("drill", slots=33))
    t.args(r3=drill)
