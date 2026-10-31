"""Synchronization packet, overflow callback, fence snapshot and cursor writes.
Worker activity has completed by the final shared-flag poll; asynchronous
hardware scheduling and a permanently busy worker are outside this spec.
"""
from liftcheck.spec import *
FUNCTION='rage_AD98'
ADDRESS=0x8235AD98
SOURCE='src/graphics/grc_command_reserve.cpp'
TRIALS=1000
_device=_replacement=0

def refill(c):
    c.write(_device+0x289C,c.rng.getrandbits(32).to_bytes(4,'big'))
    c.ret(r3=_replacement)

def thread(c):
    c.rec.derefs['device']=(c.read(_device,0x2A00),None)
    c.write(_device+0x289C,c.rng.getrandbits(32).to_bytes(4,'big'))
    c.write(_device+0x28FC,bytes(4))
    c.ret(r3=0)

def fence(c):
    c.rec.derefs['fence']=(c.read(c.r(4),4),None)
    c.write(_device+0x28FC,bytes(4))
    c.ret()

CALLS={'rage_A980':model(refill,args=('r3',)),
       'xe_GetCurrentThreadId':model(thread,args=()),
       'rage_AA78':model(fence,args=('r3','r4'))}

def inputs(t):
    global _device,_replacement
    _device=t.alloc(0x2A00,'device')
    data=t.alloc(256,'commandBufferAndGuards')
    _replacement=t.alloc(256,'replacementCommandBufferAndGuards')+16
    t.w32(_device,data+32)
    t.w32(_device+8,data+t.rng.choice([16,32,128]))
    t.w32(_device+0x289C,t.rng.choice([0,0,t.u32()]))
    t.w32(_device+0x28FC,t.rng.choice([0,1,0xFFFFFFFF]))
    t.args(r3=_device)
