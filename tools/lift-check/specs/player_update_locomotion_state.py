"""0x820CC678: assemble the player's pose and blend back into locomotion.

Priority is special/creature animation, recovery, blocked swing phase, timed
swing, secondary animation, then locomotion. Checks transition crossings,
root-motion matrices (including all four w lanes), signed frame markers,
selection/reset of the active swing record, auxiliary pose application,
early/late blend ramps, all four easing modes, per-channel blend weights,
the optional secondary overlay, and the final additive frame.

The five predicates, both normalized-time getters, frame/root-channel lookup,
frame DOF merge, copy/blend virtual dispatch, filter/ID lookup and all three
easing functions (including CRT sin/cos) execute real game code. Only the
three large animation update engines are isolated: recovery/phase/timed
advance models supply independently chosen next times, while the two timed
pose/event helpers and optional pose postprocessor are explicit boundary
stubs. Synthetic virtual animations export real frame headers; DOF callbacks
copy payloads or record blend results. Nothing is replayed from the original.

Inputs include every priority branch, competing active states, optional nulls
where legal, noncanonical boolean bytes, equality/adjacent float boundaries,
NaNs in timing comparisons, negative/zero clip durations, signed int16 frame
markers and distinct slot transforms. Frame headers and pointees are real,
nonempty sorted lists. No ignored memory and no float tolerance. Scope excludes
the isolated engines' own internal behavior, invalid graphs (the original
dereferences several nominally optional pointers), concurrency and exceptions.
Seed 1 covers 747/748 instructions in the entry's 0xBB0-byte range; the sole
unreached instruction is the count!=1 clip fallback, which reads null+12.
"""
import math
import struct

from liftcheck.spec import *

FUNCTION = "pongPlayer_C678_g"
ADDRESS = 0x820CC678
SOURCE = "src/game/player/player_animation_state.cpp"
TRIALS = 1000
FP_CONTRACT = "off"

NEXT = {}
VIRTUAL = {}


def _advance(ctx):
    obj = ctx.r(3)
    for off, value in NEXT[obj]:
        ctx.write(obj + off, struct.pack(">f", value))


def _export(ctx):
    ctx.write(ctx.r(4), ctx.read(VIRTUAL[ctx.r(3)]["frame"], 16))


def _boolean(which):
    return lambda ctx: VIRTUAL[ctx.r(3)][which]


def _position(ctx):
    ctx.ret(r3=VIRTUAL[ctx.r(3)]["position"])


def _dof_copy(ctx):
    ctx.write(ctx.r(3) + 16, ctx.read(ctx.r(4) + 16, 16))


def _dof_blend(ctx):
    # Keep the callback observable without duplicating the engine's DOF maths.
    _dof_copy(ctx)
    ctx.write(ctx.r(3) + 32, struct.pack(">f", ctx.f(1)))


CALLS = {
    **{addr: run() for addr in (
        0x820CD550, 0x820CD598, 0x820CD5F0, 0x820CD660, 0x820CD6B8,
        0x820DD238, 0x820DC8E0, 0x820CB800, 0x8224BEF8,
        0x82378450, 0x8224BB98, 0x82248250, 0x821D04F0,
        0x820CB6A0, 0x820CB6F0, 0x820CB768)},
    0x820DCDB8: model(_advance, args=("r3", "r4", "r5")),
    0x820DC540: model(_advance, args=("r3",)),
    0x820DA6F0: model(_advance, args=("r3", "r4"), deref={"r4": 0x140}),
    0x820DAC40: stub(ret="void", args=("r3", "r4"), deref={"r4": 0x140}),
    0x820DADC0: stub(ret="void", args=("r3", "r4"), deref={"r4": 0x140}),
    0x820C1E68: stub(ret="void", args=("r3", "r4"), deref={"r4": 16}),
    # r8 is dead in this callee; the original deliberately leaves it live.
    0x8224B800: run(args=("r3", "r4", "r5", "r6", "r7", "r9", "f1")),
    # These nested CRT calls have no declaration in the target TU. Their
    # contract is f1 -> f1; the incoming integer registers are unrelated noise.
    0x824301D8: run(args=("f1",)),
    0x824302B0: run(args=("f1",)),
}
for name in ("special", "secondary", "loco"):
    CALLS[name + ".vfn_3"] = stub(ret="void", args=("r3", "r4", "r5", "r6"),
                                        deref={"r5": 64}, auto_out=False)
    CALLS[name + ".vfn_4"] = stub(ret="void", args=("r3",))
    CALLS[name + ".vfn_6"] = stub(ret=_boolean("finished"), args=("r3",))
    CALLS[name + ".vfn_7"] = stub(ret=_boolean("active"), args=("r3",))
    CALLS[name + ".vfn_8"] = model(_export, args=("r3", "r4"))
CALLS["dof.vfn_6"] = model(_dof_copy, args=("r3", "r4", "r6", "f1"))
CALLS["dof.vfn_7"] = model(_dof_blend, args=("r3", "r4", "r6", "f1"))
CALLS["dof.vfn_14"] = model(_position, args=("r3",))


def f32(x):
    return struct.unpack(">f", struct.pack(">f", x))[0]


def inputs(t):
    r = t.rng
    NEXT.clear()
    VIRTUAL.clear()
    times = [-1.0, -0.0, 0.0, 0.125, 0.25, 0.4, 0.5, 0.75,
             f32(1 - 2**-24), 1.0, f32(1 + 2**-23), 1.5, math.nan]
    time = lambda: r.choice(times + [r.uniform(-0.5, 1.5)])
    # Choose priority explicitly, then occasionally enable lower priorities too.
    mode = r.randrange(6)
    state = t.alloc(0xB0, "playerState")
    dof_vt = t.vtable("dof")
    keys = [(0, 0), (1, 1), (2, 2), (5, 3)]

    def frame(addr, name):
        table = t.alloc(16, name + ".dofs")
        for i, (kind, ident) in enumerate(keys):
            dof = t.alloc(48, name + ".dof")
            t.w32(dof, dof_vt)
            t.w8(dof + 5, kind)
            t.w16(dof + 6, ident)
            t.floats(dof + 16, 8, -5, 5)
            pos = t.alloc(16, name + ".rootPosition")
            t.floats(pos, 4, -2, 2)
            VIRTUAL[dof] = {"position": pos}
            t.w32(table + 4*i, dof)
        t.w32(addr + 8, table)
        t.w16(addr + 12, 4)
        t.w16(addr + 14, r.randrange(4, 20))
        return addr

    def animation(name, size):
        obj = t.alloc(size, name)
        t.w32(obj, t.vtable(name))
        pose = frame(t.alloc(16, name + ".exportedFrame"), name + ".pose")
        VIRTUAL[obj] = {"frame": pose, "finished": 0,
                        "active": r.choice([1, 2, 0xFF, 0x101])}
        return obj

    special = animation("special", 0x100)
    secondary = animation("secondary", 0x100)
    loco = animation("loco", 0x160)
    recovery = t.alloc(0xE0, "recovery")
    phase = t.alloc(0x1B0, "phase")
    swing = t.alloc(0xA0, "swing")
    auxiliary = t.alloc(0x80, "auxiliary")
    blend = t.alloc(16, "blendFilter")
    weights = t.alloc(16, "channelWeights")
    data = t.alloc(0x20, "skeletonIds", fill="zero")
    mapping = t.alloc(16, "channelMap")
    t.w32(data + 0x14, 0)  # direct ID lookup, still run the actual helper
    t.w32(blend, data)
    t.w32(blend + 4, mapping)
    t.w32(blend + 12, weights)
    for i in range(4):
        t.w32(mapping + i*4, i)
        t.wf32(weights + i*4, r.choice([-1.0, 0.0, 0.25, 0.5, 1.0, 2.0]))
    extra = frame(t.alloc(16, "additiveFrame"), "additive")
    frame(state + 32, "output")
    frame(state + 48, "secondaryScratch")
    frame(loco + 8, "locomotion")
    frame(recovery + 128, "recovery")
    frame(phase + 384, "phase")
    frame(swing + 96, "swing")

    # Timed swing's active record is the +32 subobject of one of two slots.
    slots = []
    for i in range(2):
        slot = t.alloc(0x180, "swingSlot" + str(i))
        slots.append(slot)
        clip = t.alloc(16, "swingClip" + str(i))
        duration = r.choice([-2.0, 0.0, 0.5, 1.0, 2.0])
        t.wf32(clip + 12, duration)
        t.w32(slot + 48, clip)
        for off in (338, 340):
            t.w16(slot + off, r.choice([-32768, -3, 0, 1, 8, 16, 30, 32767]))
        t.w8(slot + 346, r.choice([0, 1, 0x80, 0xFF]))
        t.wf32(slot + 160, r.choice([0.0, 0.5, 1.0, -1.0, math.nan]))

    # Slot index is an integer here, despite the old pongPlayer header's name.
    index = r.randrange(2)
    transforms = t.alloc(19*4, "slotTransformPointers")
    for i in range(2):
        mat = t.alloc(64, "slotTransform" + str(i))
        t.floats(mat, 16, -3, 3)
        t.w32(transforms + 4*(17+i), mat)
        t.floats(0x826199A0 + i*80, 4, -4, 4)
    t.w32(0x825EAB28, transforms)
    t.w32(state + 8, index)
    t.w8(state + 19, r.choice([0, 0, 1, 0x80]))
    t.w8(state + 20, 1 if mode == 0 else 0)
    t.w32(state + 100, slots[0])
    t.w32(state + 120, slots[1])
    t.w32(state + 124, swing)
    t.w32(state + 128, recovery)
    t.w32(state + 132, auxiliary if r.choice([True, False]) else 0)
    t.w32(state + 136, phase)
    t.w32(state + 140, special)
    t.w32(state + 144, secondary if mode in (3, 4) or r.choice([True, False]) else 0)
    t.w32(state + 148, loco)
    t.w32(state + 152, blend)
    t.w32(state + 156, extra if r.choice([True, False]) else 0)
    t.wf32(state + 160, time())
    t.wf32(state + 164, time())
    t.wf32(state + 168, -123.0)
    t.w8(0x8260633C, r.choice([0, 0, 1, 0x80]))
    t.w8(0x82606334, r.choice([0, 1]))
    t.w32(0x82606330, r.choice([0, 1, 2, 3, 4, 0xFFFFFFFF]))

    # Lower priority engines may be active, but must never be called first.
    t.w8(recovery + 44, 0)
    t.wf32(recovery + 172, time() if mode <= 1 else 1.0)
    if mode == 1:
        t.w8(recovery + 44, r.choice([0, 1, 0x80]))
        t.wf32(recovery + 172, r.choice([0.25, 0.5, 0.75, math.nan]))
    t.wf32(recovery + 168, time())
    t.wf32(phase + 412, time() if mode <= 2 else 0.0)
    t.w16(phase + 90, 1 if mode == 2 else 0)
    t.wf32(phase + 96, time())
    t.wf32(phase + 100, time())
    t.wf32(swing + 28, time() if mode <= 3 else 1.0)
    t.wf32(swing + 24, time())
    t.wf32(swing + 48, 1.0)
    if mode == 3:
        t.wf32(swing + 28, r.choice([0.0, 0.25, 0.5, 0.75, math.nan]))
        t.wf32(swing + 48, r.choice([0.9, 1.0, 1.5]))
    if mode == 5:
        VIRTUAL[secondary]["finished"] = 1
    if mode == 4:
        VIRTUAL[secondary]["finished"] = 0
    t.w32(loco + 28, r.choice([0, 1, 3]))
    t.w32(loco + 32, r.choice([0, 1, 2]))
    t.w32(loco + 36, r.choice([0, 3, 4]))
    # These fields overlap loco's frame storage but not its header.
    t.w8(loco + 340, r.choice([0, 1, 0xFF]))

    for obj in (special, secondary):
        clip = t.alloc(16, "secondaryClip")
        t.wf32(clip + 12, r.choice([-1.0, 0.0, 0.5, 1.0, 2.0]))
        t.w32(obj + 84, clip)
        t.w16(obj + 88, 1)  # required by the original's unguarded clip read
        t.wf32(obj + 96, time())
    # Missing inactive engines are legal; a missing locomotion object is only
    # legal on branches that neither copy it nor blend it back into the pose.
    if mode >= 2 and r.randrange(3) == 0:
        t.w32(state + 128, 0)
    if mode >= 3 and r.randrange(3) == 0:
        t.w32(state + 136, 0)
    if mode >= 4 and r.randrange(3) == 0:
        t.w32(state + 124, 0)
    if mode == 0 and r.randrange(3) == 0:
        t.w32(state + 148, 0)
    if mode == 4 and r.randrange(3) == 0:
        t.wf32(secondary + 96, 1.0)
        t.wf32(clip + 12, 1.0)
        t.w32(state + 148, 0)
    timing = t.alloc(48, "recoveryTiming", fill="zero")
    clip = t.alloc(16, "recoveryClip")
    t.w32(timing + 36, clip)
    t.w32(timing + 32, r.choice([-4, 0, 1, 8, 15, 30, 60]))
    t.wf32(clip + 12, r.choice([-1.0, 0.0, 0.5, 1.0, 2.0]))
    t.w32(recovery + 36, timing if r.randrange(5) else 0)
    channels = t.alloc(4, "phaseChannels")
    channel = t.alloc(64, "phaseChannel")
    t.w32(channels, channel)
    t.w32(phase + 4, channels)
    t.w32(phase + 404, 0)
    t.w32(channel + 16, clip)
    t.w32(channel + 56, r.choice([-4, 0, 1, 8, 15, 30, 60]))
    NEXT[recovery] = [(168, time()), (172, time())]
    NEXT[phase] = [(96, time()), (100, time())]
    NEXT[swing] = [(28, time())]
    t.args(r3=state)
