"""0x82295598: radius extents, flagged center and refined reciprocal-root length."""
from liftcheck.spec import *
FUNCTION = 'phSphere_RebuildBounds'
ADDRESS = 0x82295598
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 600
FTOL = 1e-99
FP_CONTRACT = 'off'


def inputs(t):
    sphere = t.alloc(0x80, 'sphereAndGuards') + 16
    t.floats(sphere + 8, 14, -20, 20)
    t.w8(sphere + 5, t.pick((0, 1, 2, 0x80, 0xff)))
    if t.index % 4 == 0:
        for lane in range(3):
            t.wf32(sphere + 0x30 + lane * 4, 0)
    if t.index % 5 == 0:
        t.w32(t.pick((sphere + 8, sphere + 0x30 + 4 * t.rng.randrange(4))),
              t.pick((1, 0x807fffff, 0x7f800000, 0xff800000, 0x7fc00000, 0x80000000)))
    # Cover both the dumped zero sentinel and an initialized infinity sentinel.
    t.wf32(t.sym('lbl_82619BF0'), t.pick((0., float('inf'))))
    t.args(r3=sphere)
