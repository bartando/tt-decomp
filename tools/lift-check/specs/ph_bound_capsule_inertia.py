"""0x822A3258: hidden result r3, receiver r4, mass f1 and +70/+80 geometry."""
from liftcheck.spec import *
from specs._capsule_inertia_inputs import wrapper_inputs
FUNCTION = 'rage::phBoundCapsule::ComputeInertia'
ADDRESS = 0x822A3258
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 400
FTOL = 1e-99
FP_CONTRACT = 'off'
# r3-r5 are unused by this callee. The lift may use a local return buffer;
# compare the semantic scalar arguments, then all final result/input bytes.
CALLS = {'phCapsule_ComputeInertia': run(args=('f1', 'f2', 'f3'))}


def inputs(t):
    wrapper_inputs(t, 0x80)
