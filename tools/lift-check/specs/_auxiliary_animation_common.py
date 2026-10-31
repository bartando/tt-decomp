"""Shared synthetic auxiliary-layer states and callee effects."""
import struct
from liftcheck.spec import *

SOURCE = "src/game/player/player_auxiliary_animation_helpers.cpp"
TRIALS = 1000
EXTERNS = {"g_prngState": 0x825CA2C8, "g_kPowerBlend": 0x825C2EA0,
           "g_faceAnimDirty": 0x82606324, "g_sysTimeManager": 0x825CAEB8,
           "g_auxiliaryRandomBlendGuard": 0x825C9EC4,
           "g_auxiliaryPoseBlendGuard": 0x825C9F14}


def edge(rng):
    return rng.choice([-1.0, -0.0, 0.0, 0.25, 0.5, 1.0, 2.0,
                       float("nan"), float("inf"), -float("inf")])


def evaluate(ctx):
    # Frame +4 points back to the auxiliary state for later modeled callbacks.
    ctx.ret(r3=ctx.rng.randrange(2))


def advance(ctx):
    state, role = struct.unpack(">II", ctx.read(ctx.r(3) + 4, 8))
    if role:
        target = int.from_bytes(ctx.read(state + 0x80 + role * 4, 4), "big")
        ctx.write(state + {1: 0x44, 2: 0x4C, 3: 0x50}[role], struct.pack(">I", target))
        ctx.write(target + 0x14, struct.pack(">f", edge(ctx.rng)))
    ctx.ret(f1=edge(ctx.rng))


def blend(ctx):
    state = int.from_bytes(ctx.read(ctx.r(3) + 4, 4), "big")
    for offset in [0x44, 0x4C, 0x50]:
        entry = int.from_bytes(ctx.read(state + offset, 4), "big")
        if entry:
            ctx.write(entry + 0x14, struct.pack(">f", ctx.rng.choice([0.0, 0.25, 1.0])))


CALLS = {
    "LocomotionStateAnim_2858": model(advance),
    "LocomotionStateAnim_28B0_w": stub(ret="void"),
    "LocomotionStateAnim_88E0_g": model(evaluate, args=("r3", "r5", "r6", "r7", "f1")),
    "LocomotionStateAnim::CalculateBlendFactor": stub(ret=lambda ctx: edge(ctx.rng)),
    "rage::crAnimFrame_ApplyMatchingDofs": model(blend, args=("r3", "r4", "r5", "r6", "r7", "f1", "r9")),
    "PostGameMessage": stub(ret="void"),
    "LocomotionStateAnim_2130_g": stub(ret="void"),
}


def inputs(t):
    state = t.alloc(0xA0, "auxiliary")
    t.w8(state + 4, t.rng.choice([0, 1, 2, 0xFF]))
    t.w32(state + 8, t.rng.choice([0, 1, 7, 8, 31, 32, 63, 64, 65, -1]))
    t.wf32(state + 0x14, edge(t.rng))
    for offset in [0x34, 0x38, 0x3C]:
        frame = t.alloc(0x10, f"frame{offset:X}", fill="zero")
        t.w32(frame + 4, state)
        t.w32(state + offset, frame)

    def entry(role, name):
        obj = t.alloc(0x20, name)
        bundle = t.alloc(0x10, name + "Bundle")
        t.wf32(bundle + 0xC, edge(t.rng))
        t.w32(obj + 4, state)
        t.w32(obj + 8, role)
        t.wf32(obj + 0x14, edge(t.rng))
        t.w32(obj + 0x1C, bundle)
        return obj

    t.w32(state + 0x48, entry(0, "base"))
    for role, offset in [(1, 0x44), (2, 0x4C), (3, 0x50)]:
        obj = entry(role, f"entry{role}")
        replacement = entry(role, f"replacement{role}")
        t.w32(state + offset, obj if role == 1 or t.rng.randrange(3) else 0)
        t.w32(state + 0x80 + role * 4, replacement)
        if role == 1 and t.rng.randrange(4) == 0:
            t.w32(obj + 0x1C, 0)
    for offset in [0x54, 0x58]: t.w32(state + offset, t.alloc(0x10, f"weights{offset:X}"))
    count = t.rng.randrange(5)
    lst = t.alloc(8, "randomList")
    array = t.alloc(max(count, 1) * 4, "randomEntries")
    t.w32(lst, array)
    t.w16(lst + 4, count)
    t.w32(state + 0x94, lst)
    for i in range(count): t.w32(array + i * 4, entry(3, f"randomEntry{i}"))
    t.w32(t.sym("g_prngState"), t.rng.getrandbits(32))
    t.w32(t.sym("g_prngState") + 4, t.rng.getrandbits(32))
    t.wf32(t.sym("g_sysTimeManager") + 8, t.rng.choice([0.0, 0.0166666675, -1.0, 1.0]))
    t.wf32(t.sym("g_kPowerBlend"), edge(t.rng))
    t.w8(t.sym("g_faceAnimDirty"), t.rng.choice([0, 0, 1, 0xFF]))
    for name in ["g_auxiliaryRandomBlendGuard", "g_auxiliaryPoseBlendGuard"]:
        t.w32(t.sym(name) + 4, t.rng.choice([0, 0, 0, 1, -1]))
    t.args(r3=state)
