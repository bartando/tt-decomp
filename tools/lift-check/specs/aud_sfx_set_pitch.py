"""Log boundary, two rounded scale products, saturating command conversion.
Model the host log boundary, including +infinity; compare complete command
header, handle, parameters and guarded voice memory. The log algorithm itself
is outside this setter proof.
"""
import math
from liftcheck.spec import *
from specs._aud_sfx_command_inputs import CALLS, voice, values
FUNCTION = "rage::audVoiceSfx::SetPitch"
ADDRESS = 0x821637D8
SOURCE = "src/rage/audio/rage_audio.cpp"
TRIALS = 800
FP_CONTRACT = "off"
CALLS = {**CALLS, 0x82432458: stub(ret=lambda c: (math.log(c.f(1)) if c.f(1) > 0 else -math.inf if c.f(1) == 0 else math.nan), args=("f1",))}

def inputs(t):
    t.args(r3=voice(t), f1=values(t))
