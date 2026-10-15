"""pongAttractState::GetContext (slot 7, 0x823057E8): tail-calls the context object
(+0x08)'s slot 4 with r4 = 0. The lift used to read +0x18 (hsmState base) and null-check."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongAttractState::GetContext"
ADDRESS = 0x823057E8
SOURCE = "src/game/char_view/char_view.cpp"

CALLS = {
    "ctx.vfn_4": stub(args=("r3", "r4")),
}


def inputs(t):
    state = t.alloc(0x20, "state")
    ctx = t.alloc(0x20, "ctx")
    t.w32(ctx, t.vtable("ctx", slots=8))
    t.w32(state + 8, ctx)
    t.args(r3=state)
