"""pongCreature::ReplayStarting: replay frame position -> deferred teleport.

Reads the replay data at *0x8271A2EC (player block 0x11370 + 0xA900 * (idx != 0),
frame at +0xA8D0) and the per-player value records at *0x8271A2F0. The matrix it
builds lives on the stack; RequestTeleport takes it as a const pointer, so its
contents are compared.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreature::ReplayStarting"
ADDRESS = 0x820C5780
SOURCE = "src/game/creature/pong_creature.cpp"

CALLS = {
    "pongCreature::RequestTeleport": stub(ret="void"),
    # Supply the entire scratch matrix explicitly, as the former struct-pointer
    # declaration did. The corrected float-pointer signature otherwise infers
    # only a 4-byte output, leaving unrelated stack padding different.
    0x820C3F98: stub(ret="void", out={"r3": 64}),
    0x820C3BC8: run(),
}

REPLAY_SIZE = 0x68D00


def inputs(t):
    rng = t.rng
    idx = rng.choice([0, 1])
    creature = t.alloc(0x170, "creature")
    t.w32(creature + 0xCC, idx)

    replay = t.alloc(REPLAY_SIZE, "replay", fill="zero")
    for p in range(2):
        frame = replay + 0x11370 + 0xA900 * p + 0xA8D0
        t.floats(frame + 0x10, 4, -3.0, 3.0)                     # position (+ w)
        t.wf32(frame + 0x20, rng.choice([rng.uniform(-0.5, 1.5), 0.0, 1.0, -0.0]))
    values = t.alloc(0x40, "replayValues")
    t.floats(values, 16, -1.0, 2.0)
    t.w32(0x8271A2EC, replay)
    t.w32(0x8271A2F0, values)
    t.args(r3=creature, r4=rng.choice([0, 1]))
