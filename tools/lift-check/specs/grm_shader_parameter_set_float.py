"""Scalar writes through both packed-handle parameter banks."""
from liftcheck.spec import *
from specs._grm_parameter_write_inputs import inputs as setup

FUNCTION = "grmShaderParameter_SetFloat"
ADDRESS = 0x8215AA90
SOURCE = "src/rage/rage_grm.cpp"
TRIALS = 1000
EXTERNS = {"g_shaderParameterDirtyMasks": 0x825D4C80}

def inputs(t):
    setup(t, False)
