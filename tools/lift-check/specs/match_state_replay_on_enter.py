"""gmLogicSinglesMatch::stateReplay::onEnterState (0x8210AFD0)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmLogicSinglesMatch_stateReplay_OnEnter"
ADDRESS = 0x8210AFD0
SOURCE = "src/game/match/pong_match.cpp"

# The symbol map files game_3860 and game_76A8 under other functions of the same
# name (0x82483860, 0x823D76A8), and a comment block above a definition gives
# stateServeBounce_OnEnter a vtable address; the asm calls these.
EXTERNS = {"game_3860": 0x821D3860, "stateServeBounce_OnEnter": 0x82106A60,
           "game_76A8": 0x821676A8}

CALLS = {
    0x82106A60: stub(ret="void"),              # base OnEnter(self, 0)
    0x8225E6E0: stub(ret="void"),  # post message 0x850
    0x821D3860: stub(ret="void"),        # game_3860
    0x821676A8: stub(ret=lambda c: _swap_replay(c)),
    0x821CCE00: stub(ret="void"),
    0x8210B320: stub(ret="void"),
}

REPLAY_SIZE = 0x68D20

# The original reloads 0x8271A2EC after calling 0x821676A8; in some trials that
# callee points the global at a second replay block, so the reload shows.
_trial = {"other": 0}


def _swap_replay(ctx):
    if _trial["other"]:
        ctx.write(0x8271A2EC, _trial["other"].to_bytes(4, "big"))
    return "void"


def _replay(t, rng, name):
    replay = t.alloc(REPLAY_SIZE, name, fill="zero")
    t.w32(replay + 0x68CF4, t.u32())
    for off in (0x68CF9, 0x68CFC, 0x68CFE):
        t.w8(replay + off, rng.choice([0, 0, 1, 0x40]))
    t.w32(replay + 0x68D00, t.u32())
    return replay


def inputs(t):
    rng = t.rng
    state = t.alloc(0x20, "state")
    ctx = t.alloc(0x40, "matchContext")
    t.w8(ctx + 0x1D, rng.choice([0, 0, 1, 0x80]))
    t.w32(0x8271A2FC, ctx)

    replay = _replay(t, rng, "replay")
    _trial["other"] = _replay(t, rng, "replay2") if rng.random() < 0.3 else 0
    skip_handoff = rng.random() < 0.3
    t.w8(replay + 0x68CFB, rng.choice([1, 0x20]) if skip_handoff else 0)
    if skip_handoff and rng.random() < 0.5:
        t.w32(replay + 0x68D10, 0)
    else:
        n = rng.randrange(1, 12)
        entries = t.alloc(16 * n, "entries")
        lst = t.alloc(8, "entryList")
        t.w32(lst, entries)
        t.w16(lst + 4, n)
        t.w32(replay + 0x68D10, lst)
    t.w32(0x8271A2EC, replay)

    owner = t.alloc(0x40, "lbl_8260641C")
    t.w32(0x8260641C, owner)
    src = t.alloc(0x120, "lbl_8271A324")
    t.w32(0x8271A324, src)
    t.w32(0x8271A2F8, t.alloc(0x40, "gameState"))
    t.w8(0x82606670, rng.randrange(256))
    t.args(r3=state)
