"""Two fsel clamps, positive/negative encoding, NaN and endpoint behavior.
No tolerance or ignored bytes; compare command words and unchanged object.
"""
from specs._aud_sfx_command_inputs import CALLS, voice, values
FUNCTION = "rage::audVoiceSfx::SetPan"
ADDRESS = 0x82163868
SOURCE = "src/rage/audio/rage_audio.cpp"
TRIALS = 800
FP_CONTRACT = "off"

def inputs(t):
    t.args(r3=voice(t), f1=values(t))
