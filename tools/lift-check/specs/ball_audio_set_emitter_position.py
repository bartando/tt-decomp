"""Deferred emitter position, bit masks, denormals, NaNs and aliasing."""
from liftcheck.spec import *
FUNCTION='BallAudio_SetEmitterPosition'
ADDRESS=0x82160C98
SOURCE='src/game/ball/ball_audio_emitters.cpp'
TRIALS=1000

def inputs(t):
    r=t.rng
    emitter=t.alloc(0x90,'emitter')
    position=t.alloc(16,'position')
    vals=[0.,-0.,1e-40,-1e-40,1.,-1.,float('nan'),float('inf')]
    for i in range(4):
        x=r.choice(vals)
        t.wf32(position+4*i,x)
        t.wf32(emitter+0x60+4*i,x if t.index%3!=0 else r.choice(vals))
        t.w32(0x82619BE0+4*i,r.choice([0,0xffffffff,0x7fffffff,0xffff0000]))
    if t.index%5==1:position=emitter+0x50
    if t.index%5==2:position=emitter+0x60
    t.args(r3=emitter,r4=position)
