"""0x82465EF0: capacity checks, overwrite/shrink/clear flags and channel update.
Valid SDK rates avoid the original's division traps. Full sample storage and all
metadata are compared, including failures and caller-supplied/default formats.
"""
from liftcheck.spec import *
FUNCTION = "PcmFrame_Resize"
ADDRESS = 0x82465EF0
SOURCE = "src/platform/audio_frame.cpp"
TRIALS = 1000
def clear(c):
    c.write(c.r(3), bytes([c.r(4) & 255]) * c.r(5))
    c.ret(r3=c.r(3))
CALLS = {0x8242FED0: model(clear, transparent=True, args=("r3", "r4", "r5"))}

def inputs(t):
    r=t.rng
    owner=t.alloc(0x30,'owner',ctype='AudioFrameBuffer')
    samples=t.alloc(8*256*4,'samples')
    request=t.alloc(12,'request',ctype='AudioFrame')
    for addr in [owner+12, owner+20, request]:
        t.w8(addr,r.randrange(3)); t.w8(addr+1,r.randrange(9))
        t.w32(addr+4,r.choice([48000,24000,16000,32000]))
    t.w32(owner+28,samples)
    t.args(r3=owner,r4=r.choice([request,0]),r5=r.choice([0,1,2,3,0xFFFFFF00|r.randrange(4)]))
