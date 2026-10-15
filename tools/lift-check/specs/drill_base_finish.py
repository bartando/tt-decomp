"""pongTrainingDrill::Finish (slot 5, 0x8210CFF0): 0x5004, reticle off, final rank,
slot 28, training state 5."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongTrainingDrill::Finish"
ADDRESS = 0x8210CFF0
SOURCE = "src/game/drill/pong_drill.cpp"

CALLS = {
    "drill.vfn_27": stub(ret="void", args=("r3", "r4")),   # UpdateRank(true)
}


def inputs(t):
    rng = t.rng
    state = t.alloc(0x90, "gameState")
    active = rng.randrange(0, 4)
    t.w32(state + 0x84, active)
    player = t.alloc(0x1850, "player")
    t.w32(state + 0x74 + 4 * active, player)
    t.w32(player + 0x1840, t.alloc(0x20, "reticle") if rng.random() < 0.7 else 0)
    t.w32(0x82606430, state)
    t.w32(0x8271A34C, t.alloc(0x10, "trainingStateMachine"))
    drill = t.alloc(0x40, "drill")
    t.w32(drill, t.vtable("drill", slots=33))
    t.args(r3=drill)
