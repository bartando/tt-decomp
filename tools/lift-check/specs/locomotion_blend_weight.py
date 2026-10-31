"""0x820E6DD8: heading dispatch, live animation range and fused blend cap."""
from liftcheck.spec import *
from specs._locomotion_heading_inputs import inputs as setup, CALLS
FUNCTION = 'LocomotionStateAnim_6DD8_w'
ADDRESS = 0x820E6DD8
SOURCE = 'src/anim/locomotion_heading.cpp'
TRIALS = 1000
FP_CONTRACT = 'off'


def inputs(t):
    obj, heading = setup(t)
    t.wf32(0x825C8078, t.pick((.01, -.5, 0., .5, 1., 2.)))
    t.args(r3=obj, f1=t.pick((-1., 0., .1, .5, .9, 1., 2., float('nan'))), f2=heading)
