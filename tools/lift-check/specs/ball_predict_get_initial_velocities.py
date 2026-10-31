"""Prediction readback versus active collider fallback, including output aliasing."""
import struct
from liftcheck.spec import *
FUNCTION = "BallPredict_GetInitialVelocities"
ADDRESS = 0x821D8C70
SOURCE = "src/game/ball/ball_prediction_queries.cpp"
TRIALS = 1000


def collider(c):
    return struct.unpack(">I",c.read(c.r(3)+4,4))[0]


CALLS = {"level.vfn_4": stub(ret=collider)}


def inputs(t):
    r=t.rng
    data=t.alloc(0x2800,"prediction",ctype="gdBallPredictData")
    count=r.choice([-1,0,1,2,3,120])
    tail=r.choice([0,1,118,119,r.randrange(120)])
    t.w32(data+0x25A4,tail)
    t.w32(data+0x25A8,count)
    for i in range(120): t.floats(data+0x20+0x50*i+0x20,8,-100,100)
    instance=t.alloc(16,"instance")
    handle=r.randrange(65536)
    t.w16(instance+8,handle)
    slot=t.alloc(4,"published instance")
    t.w32(slot,instance)
    t.w32(0x8271A2F4,slot)
    sim=t.alloc(8,"simulator")
    level=t.alloc(0x20,"level")
    body=t.alloc(0x100,"collider",floats=[(0xE0,8)])
    t.floats(body+0xE0,8,-100,100)
    states=t.alloc(65536,"object states")
    t.w8(states+handle,r.choice([0,1,2,7,8,0x80,0x81,0xF8,0xFF]))
    t.w32(level,t.vtable("level",5))
    t.w32(level+4,r.choice([0,body,body]))
    t.w32(level+0x1C,states)
    t.w32(sim+4,level)
    t.w32(0x825F5BD0,sim)
    velocity=t.alloc(16,"velocity",floats=[(0,4)])
    spin=t.alloc(16,"spin",floats=[(0,4)])
    if t.index%5==0: spin=velocity
    if t.index%5==1: velocity=data+0x20+((tail+2)%120)*0x50+0x30
    if t.index%5==2: velocity=body+0xF0
    t.args(r3=data,r4=velocity,r5=spin)
