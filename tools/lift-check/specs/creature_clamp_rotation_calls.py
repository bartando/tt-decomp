"""0x82138110: quaternion -> Euler clamp -> matrix -> quaternion orchestration.

This verifies the recovered names/ABIs at the call boundaries, including every
float argument, stack pointee, and destination write. The matrix and Euler
extractor are modelled to fill their output, including matrix padding; angular
clamping is modelled at its boundary. Real FromEuler and matrix-to-quaternion
math have their own exact differential specs. Buffers may alias the bounds.
"""
import struct
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_8110_g"
ADDRESS = 0x82138110
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 600


def _matrix(ctx):
    # Deliberately initialize all lanes so stack padding can be compared.
    values = [ctx.rng.uniform(-10, 10) for _ in range(16)]
    ctx.write(ctx.r(3), struct.pack(">16f", *values))


def _angles(ctx):
    ctx.write(ctx.r(4), struct.pack(">4f", *(ctx.rng.uniform(-10, 10) for _ in range(4))))


def _from_angles(ctx):
    _matrix(ctx)


def _quaternion(ctx):
    ctx.write(ctx.r(3), struct.pack(">4f", *(ctx.rng.uniform(-1, 1) for _ in range(4))))


CALLS = {
    0x8223AD30: model(_matrix, args=("r3", "r4"), deref={"r4": 16}),
    0x82137B08: model(_angles, args=("r3", "r4"), deref={"r3": 64}),
    0x823DA1F8: stub(args=("f1", "f2", "f3")),
    0x82118278: model(_from_angles, args=("r3", "r4"), deref={"r4": 12}),
    0x8223B218: model(_quaternion, args=("r3", "r4"), deref={"r4": 64}),
}


def inputs(t):
    storage = t.alloc(112, "quaternion and bounds with guards")
    t.floats(storage, 28, -20, 20)
    quaternion = storage + 16
    lower = storage + (16 if t.index % 3 == 0 else 48)
    upper = storage + (20 if t.index % 3 == 1 else 80)
    t.args(r3=quaternion, r4=lower, r5=upper)
