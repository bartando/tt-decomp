"""_ctrlfp's raw mask merge, inverted exception-enable bits and old-value return.
Compare FPSCR as well as r3: omitting mtfsf must fail even with a correct return.
"""
from liftcheck.spec import *

FUNCTION = "_ctrlfp"
ADDRESS = 0x82436530
SOURCE = "src/crt/ctrlfp.cpp"
TRIALS = 1200
CHECK_FPSCR = True


def inputs(t):
    mask = t.pick((0, 0xffffffff, 0xf8, 3, 4, 0xFFF80700,
                   0xC007FEFF, 1 << t.rng.randrange(32), t.u32()))
    t.args(r3=t.pick((0, 0xf8, 0xffffffff, t.u32())), r4=mask,
           fpscr=t.pick((0, 1, 2, 3, 4, 0xf8, 0x82000000, t.u32())))
