"""0x82465DA8: secondary frame interface adjusts to its typed owner."""
from liftcheck.spec import *
from specs.audio_frame_get import inputs as owner_inputs
FUNCTION = "XAudioFrame_Get"
ADDRESS = 0x82465DA8
SOURCE = "src/platform/audio_frame.cpp"
TRIALS = 1000
CALLS = {"PcmFrame_Get": run(transparent=True)}
def inputs(t):
    owner_inputs(t)
    t.args(r3=t.reg_args['r3']+8)
