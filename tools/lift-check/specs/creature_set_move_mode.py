"""0x820C6CF8: creature mode entry/exit, animation callbacks and notifications."""
from liftcheck.spec import *

FUNCTION = "pg_6CF8"
ADDRESS = 0x820C6CF8
SOURCE = "src/game/player/creature_move_mode.cpp"
TRIALS = 1000
EXTERNS = {
    "g_selectionKillSignal": 0x825C9F28,
    "g_playerModeTransitionFlag": 0x82606327,
    "g_playerModeTransform": 0x82606910,
    "g_sceneRenderObj": 0x82606430,
    "g_input_obj_ptr": 0x825EAB28,
}


def speed(ctx):
    return ctx.rng.choice([0.0, 0.5, 1.0, 3.0, -1.0, float("nan"), float("inf")])


CALLS = {
    "animation.vfn_3": stub(ret="void", args=("r3",)),
    "locomotion.vfn_3": stub(ret="void", args=("r3", "r4", "r5", "r6")),
    "game_C690": stub(ret=lambda ctx: ctx.rng.randrange(2)),
    "pongMover::Reset": stub(ret="void"),
    "game_E2B8": stub(ret="void"),
    "LocomotionStateAnim_BBC8_g": stub(ret="void"),
    "pongMover_GetInputSpeed": stub(ret=speed),
    "io_Input_poll_9D68": stub(ret=lambda ctx: ctx.rng.choice([0, 1, 0x100, 0x101]),
                                preserves=("r9",)),
    "pg_E6E0": stub(ret="void"),
    "PostPageGroupMessageFmt": stub(ret="void", args=("r3", "r4", "r5", "r6")),
    "pongPlayer_7C78_g": stub(ret="void"),
}


def inputs(t):
    creature = t.alloc(0x100, "creature")
    state = t.alloc(0xA0, "state")
    mover = t.alloc(0x100, "mover")
    animation = t.alloc(16, "animation")
    locomotion = t.alloc(16, "locomotion")
    settings = t.alloc(0x300, "settings")
    table = t.alloc(0x300, "players")
    player = t.alloc(16, "outerPlayer")
    transform = t.alloc(64, "sourceTransform")
    t.w32(creature + 0xBC, state)
    t.w32(creature + 0xA8, mover)
    t.w32(state + 0x8C, animation)
    t.w32(state + 0x94, locomotion)
    t.w32(animation, t.vtable("animation"))
    t.w32(locomotion, t.vtable("locomotion"))
    modes = [0, 1, 2, 3, 4, 7, 5, -1]
    mode = modes[t.index % len(modes)]
    # All ordered mode pairs, including re-entering inactive mode seven.
    previous = modes[(t.index // len(modes)) % len(modes)]
    t.w32(creature + 0xC8, previous)
    slot = t.rng.choice([0, 1, 2, 6, 7, 31, 32, 63, 64, 65, 95])
    t.w32(creature + 0xCC, slot)
    t.w8(state + 0x14, t.rng.choice([0, 0, 1, 0xFF]))
    t.w32(mover + 0x44, t.rng.randrange(2))
    for axis in [0x30, 0x34]:
        t.wf32(mover + axis, t.rng.choice([-3.0, -0.0, 0.0, 3.0,
                                          float("nan"), t.rng.uniform(-5, 5)]))
    t.w32(t.sym("g_input_obj_ptr"), settings)
    t.w32(t.sym("g_sceneRenderObj"), table)
    t.w32(table + (slot + 0x21) * 4, 1)
    t.w32(table + 0x1E * 4, player)
    for i in range(2):
        t.w32(settings + (i + 0x11) * 4, transform)
    t.w32(settings + (slot + 14) * 4, t.rng.choice([0, 1, 1, 2]))
    t.w32(t.sym("g_selectionKillSignal") + 4, t.rng.choice([0, 1, -1]))
    t.w8(t.sym("g_playerModeTransitionFlag"), 0xA5)
    t.args(r3=creature, r4=mode)
