"""Watchdog progress/recovery, including callback changes and unsigned tick wrap.
The terminal no-diagnostic-context debugger trap is non-returning and outside
this spec; recovered hangs always retain a diagnostic context after the callback.
No ordinary return path or written bytes are ignored.
"""
from liftcheck.spec import *
FUNCTION = 'D3DDeviceXenon_ReportGPUHang'
ADDRESS = 0x823643E0
SOURCE = 'src/graphics/grc_gpu_hang.cpp'
TRIALS = 1000
EXTERNS = {'g_sda_base':0x82600000,'rage_DebugPrintf':0x82363FE0,
           'D3DDeviceXenon_DumpHangGpuState':0x82364258,
           'rage::k_str_d3d_hang_try_instrumented':0x82066510,
           'rage::k_str_d3d_hang_breaking_into_debugger':0x820665E8}
_device=_threadId=_queue=_context=0

def thread(c):
    c.write(_device+0x2888,c.rng.choice([_threadId,_threadId^1]).to_bytes(4,'big'))
    c.write(_device+0x28F8,c.rng.choice([0,1,0xFFFFFFFF]).to_bytes(4,'big'))
    c.ret(r3=_threadId)

def dump(c):
    c.write(_device+0x354C,_context.to_bytes(4,'big'))
    c.write(_device+0x289C,c.rng.getrandbits(32).to_bytes(4,'big'))
    c.write(_device+0x28C1,c.rng.getrandbits(8).to_bytes(1,'big'))
    c.write(_device+0x2890,_queue.to_bytes(4,'big'))
    c.write(0x82606654,c.rng.choice([0,0,c.rng.getrandbits(32)]).to_bytes(4,'big'))
    c.ret()

CALLS={'xe_GetCurrentThreadId':model(thread,args=()),
       'rage_DebugPrintf':stub(ret='void',args=('r3',)),
       'D3DDeviceXenon_DumpHangGpuState':model(dump,args=('r3','r4','r5','r6'))}

def inputs(t):
    global _device,_threadId,_queue,_context
    _device=t.alloc(0x5020,'device')
    state=t.alloc(44,'watchdogAndGuards')+16
    queue=t.alloc(16,'queue')
    _queue=t.alloc(16,'replacementQueue')
    _context=t.alloc(16,'replacementDiagnostics')
    ctx=t.alloc(16,'diagnosticContext')
    sda=t.alloc(0x110,'threadRoot')
    kthread=t.alloc(0x60,'kernelThread')
    t.w32(0x82600000,sda)
    t.w32(sda+0x100,kthread)
    tick=t.u32()
    head=t.u32()
    _threadId=t.u32()
    t.w32(kthread+0x58,tick)
    t.w32(queue,head)
    t.w32(_device+0x2890,queue)
    t.w32(_device+0x2888,t.rng.choice([_threadId,_threadId^1]))
    t.w32(_device+0x28F8,t.rng.choice([0,1]))
    t.w8(_device+0x28C1,t.rng.randrange(256)&~4 | (4 if t.index%8==0 else 0))
    t.w32(_device+0x354C,t.rng.choice([0,ctx]))
    t.w32(state,_device)
    t.w32(state+4,tick-t.rng.choice([0,1999,2000,2001,0xFFFFFFFF]))
    t.w32(state+8,t.rng.choice([head,head,head^1]))
    t.args(r3=state,r13=sda)
