"""0x820CBBC8: optional blender reset, RNG delay, callbacks and frame reapplication."""
import struct
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_BBC8_g"
ADDRESS = 0x820CBBC8
SOURCE = "src/game/player/player_mode_animation.cpp"
TRIALS = 1000
EXTERNS = {
    "g_swingInFlightFlag": 0x8260633C,
    "g_swingCountFlag": 0x82606340,
    "g_input_obj_ptr": 0x825EAB28,
    "g_prngState": 0x825CA2C8,
    "g_faceAnimDirty": 0x82606324,
    "g_kPowerBlend": 0x825C2EA0,
    "lbl_825C5938": 0x825C5938,
    "g_playerModeAnimationBytes": 0x825EAB48,
    "g_playerModeAnimationPairParams": 0x825CB850,
}


def clear_record(ctx):
    state, next_offset = struct.unpack(">II", ctx.read(ctx.r(3) - 0x1C, 8))
    if next_offset:
        ctx.write(state + next_offset, bytes(4))


def choose_face(ctx):
    # The selection routine consumes the same shared generator first.
    ctx.write(0x825CA2C8, struct.pack(">II", ctx.rng.getrandbits(32), ctx.rng.getrandbits(32)))


def apply_frame(ctx):
    state, replacement = struct.unpack(">II", ctx.read(ctx.r(3) + 4, 8))
    ctx.write(state + 0x48, struct.pack(">I", replacement))
    ctx.write(state + 0x4C, bytes(2))


def pair(ctx):
    # The mask reset uses the slot after this callback, not its entry value.
    ctx.write(ctx.r(3) - 0x40 + 8, struct.pack(">I", ctx.rng.randrange(2)))
    ctx.ret(r3=ctx.rng.randrange(2))


CALLS = {
    "LocomotionStateAnim_6D48": model(clear_record),
    "game_CD20": stub(ret="void"),
    "crAnimBlenderState_Init": stub(ret="void"),
    "secondary.vfn_3": stub(ret="void", args=("r3",)),
    "special.vfn_3": stub(ret="void", args=("r3",)),
    "locomotion.vfn_3": stub(ret="void", args=("r3", "r4", "r5", "r6"), deref={"r5": 64}),
    "LocomotionStateAnim_2130_g": model(choose_face),
    "LocomotionStateAnim_BlendLocomotionAnims": model(apply_frame, args=("r3", "r5", "f1")),
    "LocomotionStateAnim_TransitionLocomotionState": model(apply_frame, args=("r3", "r5", "f1")),
    "LocomotionStateAnim::SetupAnimationPair": model(pair, args=("r3", "r4", "r5", "r7"), deref={"r7": 32}),
}


def inputs(t):
    state = t.alloc(0xC0, "state")
    t.w32(state + 8, t.rng.randrange(2))
    for offset in [0x64, 0x68, 0x6C, 0x70, 0x74]:
        record = t.alloc(0x1A0, f"record{offset:X}") if t.rng.randrange(3) else 0
        t.w32(state + offset, record)
        if record:
            t.w32(record + 4, state)
            t.w32(record + 8, offset + 4 if offset < 0x74 and t.rng.randrange(2) else 0)
    for offset, size in [(0x7C, 0x90), (0x80, 0xD4), (0x88, 0x1A0), (0x84, 0xA0)]:
        obj = t.alloc(size, f"state{offset:X}") if t.rng.randrange(3) else 0
        t.w32(state + offset, obj)
        if obj and offset == 0x84:
            child = t.alloc(0x20, "activeFace") if t.rng.randrange(2) else 0
            t.w32(obj + 0x44, child)
            if child: t.wf32(child + 0x14, t.rng.uniform(-2, 2))
    for offset, name, optional in [(0x8C, "special", False), (0x90, "secondary", True), (0x94, "locomotion", True)]:
        obj = t.alloc(0x10, name) if not optional or t.rng.randrange(3) else 0
        t.w32(state + offset, obj)
        if obj: t.w32(obj, t.vtable(name))
    settings = t.alloc(0x60, "settings")
    t.w32(t.sym("g_input_obj_ptr"), settings)
    for slot in range(2):
        t.w32(settings + (slot + 17) * 4, t.alloc(64, f"transform{slot}"))
    skeleton = t.alloc(0x20, "skeleton")
    data = t.alloc(0x20, "skeletonData")
    t.w32(state + 0x1C, skeleton)
    t.w32(skeleton + 4, data)
    t.w32(data + 0x14, t.rng.getrandbits(32))
    count = t.index % 5
    entries = [t.alloc(16, f"entries{i}") for i in range(2)]
    t.w32(state + 0x48, entries[0])
    t.w16(state + 0x4C, count)
    channels = []
    for i in range(4):
        entry = t.alloc(16, f"entry{i}")
        channels.append(entry)
        t.w32(entry + 4, state)
        t.w32(entry + 8, entries[1])
    for i in range(4):
        t.w32(entries[0] + i * 4, channels[i])
        t.w32(entries[1] + i * 4, channels[3 - i])
    t.w32(t.sym("g_prngState"), t.rng.getrandbits(32))
    t.w32(t.sym("g_prngState") + 4, t.rng.getrandbits(32))
    t.w8(t.sym("g_swingInFlightFlag"), 0xA5)
    t.w32(t.sym("g_swingCountFlag"), 0xDEADBEEF)
    t.w8(t.sym("g_faceAnimDirty"), 0xFF)
    t.wf32(t.sym("g_kPowerBlend"), t.rng.uniform(-3, 3))
    t.wf32(t.sym("lbl_825C5938"), t.rng.uniform(-2, 2))
    for i in range(28): t.w8(t.sym("g_playerModeAnimationBytes") + i, 0xA5)
    t.floats(t.sym("g_playerModeAnimationPairParams"), 8, -2, 2)
    t.args(r3=state)
