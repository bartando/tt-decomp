"""pongCreature::UpdateReplay: replay frame -> instance, animations, teleport, workers.

Covers: the instance's slot-3 call and the level's slot-11 call, the player
state's [0, 1] test that swaps in game_C5A8's list, the per-entry apply through
0x8224C128 or 0x8224C288 (skeleton flag bit 0), the clamped replay value, the
deferred teleport (with and without the hold flag) and the two workers.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreature::UpdateReplay"
ADDRESS = 0x820C59C0
SOURCE = "src/game/creature/pong_creature.cpp"

LIST_FROM_STATE = {}

CALLS = {
    "inst.vfn_3": stub(ret="void", args=("r3", "r4")),     # SetLastMatrix(inst, inst + 0x10)
    "level.vfn_11": stub(ret="void", args=("r3", "r4")),   # UpdateObjectLocation(level, index)
    0x820CC5A8: model(lambda ctx: ctx.ret(r3=LIST_FROM_STATE["v"])),
    # The apply callees take (entry, ?, skeleton, weight). The original leaves
    # whatever was in r4; the lift passes null. Neither callee reads r4.
    0x8224C128: stub(ret="void", args=("r3", "r5", "f1")),
    0x8224C288: stub(ret="void", args=("r3", "r5", "f1")),
}

REPLAY_SIZE = 0x68D00


def anim_list(t, addr, name):
    n = t.rng.choice([0, 1, 3])
    entries = t.alloc(4 * max(n, 1), name + ".entries")
    t.w32(addr + 0x08, entries)
    t.w16(addr + 0x0C, n)


def inputs(t):
    rng = t.rng
    idx = rng.choice([0, 1])
    creature = t.alloc(0x170, "creature")
    t.w32(creature + 0xCC, idx)

    inst = t.alloc(0x130, "inst")
    t.w32(inst, t.vtable("inst", 48))
    t.floats(inst + 0x10, 16, -5.0, 5.0)
    t.w32(creature + 0xA4, inst)

    level = t.alloc(0x40, "level")
    t.w32(level, t.vtable("level", 16))
    t.w32(0x826065E4, level)

    state = t.alloc(0xC0, "state")
    t.wf32(state + 0xB0, rng.choice([rng.uniform(-0.5, 1.5), 0.0, 1.0, float("nan")]))
    t.w32(creature + 0xBC, state)

    skel_data = t.alloc(0x20, "skeletonData")
    t.w32(skel_data + 0x14, rng.getrandbits(32))
    skeleton = t.alloc(0x20, "skeleton")
    t.w32(skeleton + 0x04, skel_data)
    t.w32(creature + 0xAC, skeleton)

    replay = t.alloc(REPLAY_SIZE, "replay", fill="zero")
    for p in range(2):
        frame = replay + 0x11370 + 0xA900 * p + 0xA8D0
        t.floats(frame + 0x10, 4, -3.0, 3.0)
        t.wf32(frame + 0x20, rng.choice([rng.uniform(-0.5, 1.5), 0.0, 1.0]))
        anim_list(t, replay + 0x68C6C + 0x30 * p, f"replayList{p}")
    values = t.alloc(0x40, "replayValues")
    t.floats(values, 16, -1.0, 2.0)
    t.w32(0x8271A2EC, replay)
    t.w32(0x8271A2F0, values)

    other = t.alloc(0x10, "stateList")
    anim_list(t, other, "stateList")
    LIST_FROM_STATE["v"] = other

    data = t.alloc(0xE0, "charData")
    for k in range(2):
        if rng.random() < 0.7:
            w = t.alloc(0x80, f"worker{k}")
            t.w32(data + 0xD8 + 4 * k, w)
        else:
            t.w32(data + 0xD8 + 4 * k, 0)
    char = t.alloc(0x20, "char")
    t.w32(char + 0x14, data)
    t.w32(creature + 0xA0, char)

    t.w8(creature + 0xE5, rng.choice([0, 1]))
    t.floats(creature + 0x110, 16, -5.0, 5.0)
    t.w8(creature + 0x150, rng.choice([0, 1]))
    t.w8(creature + 0x151, rng.choice([0, 1]))
    t.w8(creature + 0x152, rng.choice([0, 1]))
    t.args(r3=creature)
