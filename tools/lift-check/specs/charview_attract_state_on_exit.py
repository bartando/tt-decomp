"""pongAttractState::OnExit (slot 8, 0x82306EA8): releases the context object at +0x08
(its slot 5), deletes it (slot 0, flags 1) if the release left it set, clears +0x08."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongAttractState::OnExit"
ADDRESS = 0x82306EA8
SOURCE = "src/game/char_view/char_view.cpp"



_trial = {"state": 0, "clear": False}


def _release(ctx):
    if _trial["clear"]:  # the release can drop the owner's pointer
        ctx.write(_trial["state"] + 8, b"\0\0\0\0")
    ctx.ret()


CALLS = {
    "ctx.vfn_5": model(_release),
    "ctx.vfn_0": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    state = t.alloc(0x20, "state")
    ctx = t.alloc(0x20, "ctx")
    t.w32(ctx, t.vtable("ctx", slots=8))
    t.w32(state + 8, t.rng.choice([0, ctx, ctx, ctx]))
    _trial.update(state=state, clear=t.rng.random() < 0.3)
    t.args(r3=state)
