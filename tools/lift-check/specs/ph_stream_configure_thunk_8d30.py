"""0x82468D30: forward float output and preserve all adjacent bytes."""
from liftcheck.spec import *
FUNCTION = 'rage::ph_vt5A60_33_Thunk'
ADDRESS = 0x82468D30
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 200
FTOL = 1e-99
CALLS = {'rage::ph_vt5A78_63_GetFloat108': run()}


def inputs(t):
    owner = t.alloc(0x100, 'ownerAndGuards') + 16
    t.wf32(owner + 0x6c, t.pick((0., -0., 1e-40, float('inf'), float('nan'), t.f32())))
    output = t.pick((owner + 0x6c, owner + 0x70, t.alloc(32, 'outputAndGuards') + 12))
    t.float_words.add(output)
    t.args(r3=owner + 16, r4=output)
