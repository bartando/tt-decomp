"""0x8224F0E0: transpose root basis, accumulate origin, rebase body positions.

Root/collider aliasing, arbitrary basis/W, cached vs current angular velocities,
nonpositive counts, repeated bodies, subnormals/nonfinites, and guards.
"""
from liftcheck.spec import *
from specs._articulated_step_inputs import bodies

FUNCTION = "phArticulatedCollider_F0E0"
ADDRESS = 0x8224F0E0
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 600
FP_CONTRACT = "off"
FTOL = 1e-99


def inputs(t):
    rng = t.rng
    data, array = bodies(t)
    collider = t.alloc(0x480, 'colliderAndGuards') + 16
    t.floats(collider, 0x460 // 4, -20, 20)
    if t.index % 7 == 0:
        collider = array[0]
    t.w32(collider + 0x1D0, data)
    if t.index % 5 == 0:
        t.w32(rng.choice(array) + rng.choice((0x90, 0xC0, 0x130, 0x140)) + 4 * rng.randrange(4),
              rng.choice((1, 0x807FFFFF, 0x00800000, 0x7F800000, 0xFF800000, 0x7FC00000)))
    if t.index % 3 == 0:
        t.floats(t.sym('lbl_82606750'), 4, -2, 2)
    t.args(r3=collider)
