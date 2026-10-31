"""fctidz low-word stores; include values beyond int32 and int64 ranges.
Compare both parameter words, command header, handle and source/guard memory.
"""
from liftcheck.spec import *
from specs._aud_sfx_command_inputs import voice, values
FUNCTION = "rage::audVoiceSfx::SetStereoVolume"
ADDRESS = 0x82163938
SOURCE = "src/rage/audio/rage_audio.cpp"
TRIALS = 800
FP_CONTRACT = "off"
CALLS = {0x821AAEE8: stub(ret="void", args=("r3", "r4", "r5", "r6"), deref={"r5": 12})}

def inputs(t):
    t.args(r3=voice(t), f1=values(t), f2=values(t))
