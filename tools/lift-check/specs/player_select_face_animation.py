"""0x820C2130: active timer reset and non-neutral random face selection."""
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_2130_g"
ADDRESS = 0x820C2130
SOURCE = "src/game/player/player_animation_reset_helpers.cpp"
TRIALS = 1000
EXTERNS = {"g_loop_obj_ptr": 0x825EAB30, "g_prngState": 0x825CA2C8,
           "g_faceAnimationSelectionGuard": 0x825C9F00}


def inputs(t):
    face = t.alloc(0xA0, "face")
    loop = t.alloc(0x250, "loop")
    t.w32(t.sym("g_loop_obj_ptr"), loop)
    t.w8(loop + 0x240, t.rng.choice([0, 1, 2, 0x80, 0xFF]))
    current = t.alloc(0x20, "current") if t.rng.randrange(2) else 0
    t.w32(face + 0x4C, current)
    if current: t.wf32(current + 0x14, t.rng.uniform(-5, 5))
    for offset in [0x98, 0x9C]:
        count = t.rng.choice([0, 1, 2, 3, 5, 16, 0xFFFF if t.index % 100 == 0 else 8])
        array = t.alloc(max(count, 1) * 4, f"entries{offset:X}")
        lst = t.alloc(8, f"list{offset:X}")
        t.w32(lst, array)
        t.w16(lst + 4, count)
        t.w32(face + offset, lst)
    t.w32(t.sym("g_faceAnimationSelectionGuard") + 4, t.rng.choice([0, 0, 0, 1, -1]))
    t.w32(t.sym("g_prngState"), t.rng.getrandbits(32))
    t.w32(t.sym("g_prngState") + 4, t.rng.getrandbits(32))
    t.args(r3=face)
