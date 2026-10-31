"""Reserve callback writes, emergency imports and pending fence snapshots.
Both process types, zero/overflow requests, failed/successful callbacks, adjusted
sizes and both fence slots are covered. Kernel/driver calls are observed
boundaries; every game-memory write compares without ignored ranges.
"""
from liftcheck.spec import *
_device=0
_result=0
_adjusted=0


def process(c): c.ret(r3=c.rng.choice([1,2]))
def reserve(c):
    c.rec.derefs['bytes']=(c.read(c.r(6),4),None)
    c.rec.derefs['device']=(c.read(_device,0x5100),None)
    c.write(c.r(6),_adjusted.to_bytes(4,'big'))
    c.write(_device+0x5070,c.rng.getrandbits(32).to_bytes(4,'big'))
    c.write(_device+0x36D8,c.rng.choice([0,0,c.rng.getrandbits(32)]).to_bytes(4,'big'))
    c.write(_device+0x36DC,c.rng.choice([0,0,c.rng.getrandbits(32)]).to_bytes(4,'big'))
    c.ret(r3=_result)

def thread(c):
    c.write(_device+0x36D8,c.rng.getrandbits(32).to_bytes(4,'big'))
    c.write(_device+0x36DC,c.rng.getrandbits(32).to_bytes(4,'big'))
    c.write(_device+0x5070,c.rng.getrandbits(32).to_bytes(4,'big'))
    c.ret(r3=c.rng.getrandbits(32))

def fence(c):
    c.rec.derefs['fence']=(c.read(c.r(4),4),None)
    c.write(c.r(4),c.rng.getrandbits(32).to_bytes(4,'big'))
    c.write(_device+0x36D8,c.rng.getrandbits(32).to_bytes(4,'big'))
    c.write(_device+0x36DC,c.rng.getrandbits(32).to_bytes(4,'big'))
    c.ret()

CALLS={'KeGetCurrentProcessType':model(process,args=()),
       'reserve':model(reserve,args=('r3','r4','r5','r6','r7')),
       'xe_GetCurrentThreadId':model(thread,args=()),
       'rage_AA78':model(fence,args=('r3','r4')),
       'grcDevice_UseEmergencyCommandBuffer':run()}


def device_input(t):
    global _device
    _device=t.alloc(0x5100,'device')
    for address in [0x82000730,0x82000734]:
        owner=t.alloc(0x3D20,'globalDevice')
        command=t.alloc(0x1300,'emergencyBuffer')
        slot=t.alloc(4,'importedGlobalDeviceSlot')
        t.w32(address,slot)
        t.w32(slot,owner)
        t.w32(owner+0x3D1C,command)
    t.args(r3=_device)


def reserve_input(t):
    global _result,_adjusted
    device_input(t)
    r=t.rng
    result=t.alloc(0x2200,'commandAllocationAndGuards')+0x100
    _result=r.choice([0,0,result])
    _adjusted=r.choice([0,1,4,48,128,512,4099])
    t.w32(_device+0x3544,t.fake_fn('reserve'))
    t.w32(_device+0x3548,t.alloc(16,'reserveContext'))
    t.w8(_device+0x28C1,r.randrange(256))
    t.w32(_device+0x5070,t.u32())
    t.w32(_device+0x36D8,r.choice([0,t.u32()]))
    t.w32(_device+0x36DC,r.choice([0,t.u32()]))
    t.args(r4=r.choice([0,1,12,0x3FFFFFF4,0x40000000,0xFFFFFFFF,t.u32()]))
