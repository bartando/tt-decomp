"""Fence wrap, submit-on-equality, moving consumers and persistent watchdog.
No asynchronous hardware is required: watchdog callbacks update queues, abort or
release the fence, and mutate their state. Every write and call argument compares.
"""
from liftcheck.spec import *
_device=_fence=_tick=0
_queues=[]
_calls={}
_mode=0


def refill(c):
    producer=c.rng.getrandbits(32)
    c.write(_device+0x289C,producer.to_bytes(4,'big'))
    c.write(_fence,producer.to_bytes(4,'big'))
    queue=c.rng.choice(_queues)
    c.write(_device+0x2890,queue.to_bytes(4,'big'))
    c.write(queue,((producer-64) & 0xFFFFFFFF).to_bytes(4,'big'))
    c.ret(r3=0)


def watchdog(c):
    n=_calls.get(c.side,0)
    _calls[c.side]=n+1
    assert n < 4, 'fence wait did not observe progress'
    p=c.r(3)
    c.rec.derefs['state']=(c.read(p,12),None)
    c.write(p+4,(0x12340001+n).to_bytes(4,'big'))
    c.write(p+8,(0x56780001+n).to_bytes(4,'big'))
    producer=c.rng.getrandbits(32)
    c.write(_device+0x289C,producer.to_bytes(4,'big'))
    c.write(_fence,producer.to_bytes(4,'big'))
    queue=c.rng.choice(_queues)
    c.write(_device+0x2890,queue.to_bytes(4,'big'))
    c.write(queue,((producer-(64 if n<_mode else 0)) & 0xFFFFFFFF).to_bytes(4,'big'))
    c.ret(r3=0 if _mode==3 and n==1 else 1)

CALLS={'rage_A980':model(refill,args=('r3',)),
       'D3DDeviceXenon_ReportGPUHang':model(watchdog,args=('r3',))}

def inputs(t):
    global _device,_fence,_tick,_queues,_calls,_mode
    _calls={}
    _mode=t.index%4
    _device=t.alloc(0x3800,'device')
    _fence=t.alloc(16,'fenceAndGuards')
    _queues=[t.alloc(16,f'consumer{i}') for i in range(3)]
    sda=t.alloc(0x110,'threadRoot')
    thread=t.alloc(0x60,'kernelThread')
    t.w32(0x82600000,sda)
    t.w32(sda+0x100,thread)
    _tick=t.u32()
    t.w32(thread+0x58,_tick)
    producer=t.u32()
    age=t.rng.choice([0,0,1,64,0x7FFFFFFF,0xFFFFFFFC])
    lag=(age+t.rng.choice([-1,0,1,64])) & 0xFFFFFFFF
    t.w32(_device+0x289C,producer)
    t.w32(_device+0x2890,_queues[0])
    t.w32(_device+0x34E0,t.rng.choice([0,0,1,0x80000000]))
    t.w32(_queues[0],producer-lag)
    t.w32(_fence,producer-age)
    t.args(r3=_device,r4=_fence,r13=sda)
