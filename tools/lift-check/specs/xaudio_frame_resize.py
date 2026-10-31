"""0x82466018: frame interface adjustment, with the real resize body."""
from liftcheck.spec import *
from specs.audio_frame_resize import inputs as owner_inputs, clear
FUNCTION = "XAudioFrame_Resize"
ADDRESS = 0x82466018
SOURCE = "src/platform/audio_frame.cpp"
TRIALS = 1000
CALLS = {"PcmFrame_Resize": run(transparent=True), 0x8242FED0: model(clear, transparent=True, args=("r3", "r4", "r5"))}
def inputs(t):
    owner_inputs(t)
    t.args(r3=t.reg_args['r3']+8)
