"""0x820C1E68: guarded facial pose update, deadline notification and DOF blend."""
import struct
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_1E68_g"
ADDRESS = 0x820C1E68
SOURCE = "src/game/player/player_auxiliary_pose.cpp"
TRIALS = 1000
EXTERNS = {"g_matMgrGuard": 0x825C9EB0, "g_auxiliaryPoseBlendGuard": 0x825C9F14,
           "g_pongMatchTiming": 0x8271A2E8}


def update(ctx):
    # The update can select a new active animation before the deadline check.
    ctx.write(ctx.r(3) + 0x44, ctx.read(ctx.r(3) + 0x90, 4))


def select(ctx):
    # Pose/filter data must be read after selector callbacks.
    frame, weights = struct.unpack(">II", ctx.read(ctx.r(3) + 0x94, 8))
    ctx.write(ctx.r(3) + 0x34, struct.pack(">I", frame))
    ctx.write(ctx.r(3) + 0x54, struct.pack(">I", weights))


CALLS = {
    "LocomotionStateAnim_1CE8_g": model(update),
    "LocomotionStateAnim_1B90": model(select),
    "LocomotionStateAnim_1978": model(select),
    "pg_E6E0_msg": stub(ret="void", args=("r3", "r4", "r5", "r6")),
    "rage::crAnimFrame_ApplyMatchingDofs": stub(
        ret="void", args=("r3", "r4", "r5", "r6", "r7", "f1", "r9")),
}


def inputs(t):
    state = t.alloc(0xA0, "auxiliary")
    out = t.alloc(0x10, "destination")
    active = t.alloc(0x20, "active")
    name = t.alloc(1080, "clipName", fill="zero")
    length = t.rng.choice([0, 1, 3, 4, 7, 15, 31, 1020, 1021, 1024, 1030])
    t.put(name, bytes([65 + t.index % 26]) * length + b"\0")
    t.w32(active + 0x18, name)
    t.w8(state + 4, t.rng.choice([0, 1, 1, 2, 0xFF]))
    t.w32(state + 8, t.rng.choice([0, 1, -1]))
    t.w32(state + 0x44, t.rng.choice([0, active]))
    t.w32(state + 0x90, t.rng.choice([0, active]))
    t.w32(state + 0x34, t.alloc(0x10, "oldPose", fill="zero"))
    t.w32(state + 0x54, t.alloc(0x10, "oldWeights"))
    t.w32(state + 0x94, t.alloc(0x10, "newPose", fill="zero"))
    t.w32(state + 0x98, t.alloc(0x10, "newWeights"))
    clock = t.alloc(0x40, "clock")
    t.w32(t.sym("g_pongMatchTiming"), clock)
    deadline = t.rng.choice([-1.0, -0.0, 0.0, 0.5, 1.0, float("nan"), float("inf")])
    t.wf32(state + 0x18, deadline)
    t.wf32(clock + 0x30, t.rng.choice([deadline, -1.0, 0.0, 0.5, 1.0, 2.0, float("nan")]))
    t.w32(t.sym("g_matMgrGuard") + 4, t.rng.choice([0, 0, 0, 1, -1]))
    t.w32(t.sym("g_auxiliaryPoseBlendGuard") + 4, t.rng.choice([0, 0, 1, -1]))
    t.args(r3=state, r4=out)
