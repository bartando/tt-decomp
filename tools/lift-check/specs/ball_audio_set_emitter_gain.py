"""Gain threshold, clamp, unordered values and dirty flag after logging."""
import struct
from liftcheck.spec import *
FUNCTION='BallAudio_SetEmitterGain'
ADDRESS=0x82162218
SOURCE='src/game/ball/ball_audio_emitters.cpp'
TRIALS=1000

def log(ctx):
    p=struct.unpack(">I",ctx.read(0x825EAB28,4))[0]
    ctx.write(p+0x14,struct.pack(">I",0x12345670))
    ctx.ret()

CALLS={'nop_8240E6D0':model(log,args=('r3',))}

def inputs(t):
    r=t.rng
    t.emitter=t.alloc(0x90,'emitter',floats=[(0x20,1)])
    t.w32(0x825EAB28,t.emitter)
    old=r.choice([0.,0.5,1.,float('nan')])
    t.wf32(t.emitter+0x20,old)
    value=r.choice([old,old+0.004,old+0.005,old+0.006,-0.1,1.1,0.,1.,float('nan'),float('inf'),-float('inf')])
    t.args(r3=t.emitter,f1=value)
