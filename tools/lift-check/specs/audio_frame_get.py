"""0x82465D80: copy the current SDK frame descriptor with its sample pointer."""
from liftcheck.spec import *
FUNCTION = "PcmFrame_Get"
ADDRESS = 0x82465D80
SOURCE = "src/platform/audio_frame.cpp"
TRIALS = 1000

def inputs(t):
    owner = t.alloc(0x40, 'owner', ctype='AudioFrameBuffer')
    out = t.alloc(12, 'out', ctype='AudioFrame')
    t.args(r3=owner, r4=out)
