"""Open failures/vetoes, fixed stream pool exhaustion/reuse, and scope flags.
Callbacks model the backend and kernel boundaries; no memory is ignored.
"""
from liftcheck.spec import *
_device = 0
_result = 0
_callback = 0
_scope_flag = 0


def resolve(c): c.ret(r3=_device)
def construct(c): c.ret(r3=_result)
def device_open(c): c.ret(r3=c.rng.choice([-1, -2, 0, 1, c.rng.getrandbits(32)]))
def callback(c): c.ret(r3=c.rng.choice([0, 1, 0x100, 0x101, 0xffffffff]))
def log(c):
    c.write(0x825F5CF0, c.rng.choice([0, _callback]).to_bytes(4,'big'))
    c.ret()
OPEN_CALLS = {
    'fiDevice_GetDevice': model(resolve,args=('r3','r4')),
    'device.vfn_1': model(device_open,args=('r3','r4','r5')),
    'device.vfn_6': stub(ret='void',args=('r3','r4')),
    'nop_8240E6D0':model(log,args=('r3','r4','r5','r6','r7')),
    'openCallback':model(callback,args=('r3','r4')),
    'fiStreamBuf_Attach':model(construct,args=('r3','r4','r5')),
    'fiStreamBuf_OpenFailed':stub(ret=0,args=('r3',)),
}

def open_input(t):
    global _device,_result,_callback
    _device = t.alloc(16,'device') if t.rng.randrange(4) else 0
    if _device: t.w32(_device,t.vtable('device',slots=9))
    _result=t.rng.choice([0,t.alloc(28,'stream')])
    _callback=t.fake_fn('openCallback')
    t.w32(0x825F5CF0,t.rng.choice([0,_callback]))
    t.w32(0x825F5CF8,t.u32())
    path=t.alloc(32,'path',fill=b'game:/test.txt\0'+bytes(17))
    t.args(r3=path,r4=t.u32())


def scope_enter(c):
    c.write(c.r(3), bytes([_scope_flag]))
    c.ret()

POOL_CALLS = {
    'fiStreamLock_Acquire':model(scope_enter,args=('r3',)),
    'fiStreamLock_Release':run(),
    'RtlInitializeCriticalSection':stub(ret=0,args=('r3',)),
    'RtlLeaveCriticalSection':stub(ret='void',args=('r3',)),
    'xe_atexit':stub(ret=0,args=('r3',)),
    'rage_DebugLog':stub(ret='void',args=('r3',)),
}

def pool_input(t):
    global _scope_flag
    _scope_flag=t.rng.choice([0,1,1,2,255])
    t.w32(0x8271B230,t.u32())
    t.w32(0x825C4818,t.rng.choice([-1,0,1,4,11,12]))
    device=t.alloc(16,'device')
    first_free=t.rng.randrange(14)
    for i in range(12):
        t.w32(0x825F5D00+i*28,0 if i==first_free or (i>first_free and t.rng.randrange(2)) else device)
    t.args(r3=0,r4=t.u32(),r5=device)


def failed_input(t):
    t.w32(0x825D06B4,t.rng.choice([0,t.alloc(16,'option')]))
    t.args(r3=t.alloc(32,'path',fill=b'game:/missing.txt\0'+bytes(14)))

FAILED_CALLS={'rage_DebugLog':stub(ret='void',args=('r3','r4'))}
SCOPE_CALLS={'RtlEnterCriticalSection':stub(ret='void',args=('r3',)),
             'RtlLeaveCriticalSection':stub(ret='void',args=('r3',))}
def scope_input(t):
    scope=t.alloc(40,'scopeAndGuards')+16
    t.w8(scope,t.rng.choice([0,1,1,2,255]))
    t.w32(scope+4,t.alloc(32,'criticalSection'))
    t.args(r3=scope)
