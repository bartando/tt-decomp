from liftcheck.spec import *
SOURCE='src/rage/audio/xact_wave_acquire.cpp'
TRIALS=800
def _acquire(c):
    status=c.rng.choice([0,0,1,0xFFFFFFFF,0x8007000E])
    if c.r(5): c.write(c.r(5),(0x45000800).to_bytes(4,'big'))
    c.ret(r3=status)
def _set_float(c):
    # Xenon reserves r4 for the middle float; compiled PPC32 SysV packs the
    # following integer into r4. Normalize that ABI gap, then compare flags
    # in Xenon's r5. A nonzero-flag mutation must still fail this boundary.
    flags=c.r(5) if c.side=='orig' else c.r(4)
    c.rec.gpr[2]=flags
    c.rec.gpr64[2]=flags
    c.ret()
CALLS={'RtlEnterCriticalSection':stub(ret='void',args=('r3',)),
       'RtlLeaveCriticalSection':stub(ret='void',args=('r3',)),
       'bank.vfn_11':stub(ret=0x45000000,args=('r3','r4')),
       'bank.vfn_2':stub(ret=0x45000040,args=('r3','r4')),
       'xactBank_GetWaveRecord':run(),
       'msgMsgSink_EC28_g':model(_acquire,args=('r3','r4','r6'),deref={'r5':4}),
       'msgMsgSink_84C0_gen':stub(ret=lambda c:c.rng.choice([0,0,1,0xFFFFFFFF,0x80000000])),
       'msgSlot_SetFloat':model(_set_float,args=('r3','f1','r5'))}
def owner(t,nullable=True):
    data=t.map(0x45000000,0x4000,'header, descriptor, variable and wave records')
    t.w16(data+0xB,t.rng.randrange(11))
    t.w8(data+0x40,t.rng.randrange(256))
    t.w32(data+0x800+0x10,data+0x40)
    t.wf32(data+0x800+0x14,t.rng.choice([0.0,1.0,-1.0,0.5,float('nan')]))
    context=t.alloc(0xC0,'context')
    bank=t.alloc(0x80,'bank')
    t.w32(bank,t.vtable('bank',12))
    t.w32(bank+0x7C,data+0x1000)
    t.w32(context+0x7C,t.rng.choice([0,bank,bank]) if nullable else bank)
    return context
def cue(t):
    context=owner(t)
    cue=t.alloc(0x180,'cue')
    link=t.alloc(12,'link')
    descriptor=t.alloc(12,'cue descriptor')
    t.w16(descriptor+6,t.rng.randrange(12))
    t.w32(link+8,descriptor)
    t.w32(cue+0x120,link)
    t.w32(cue+0x38,context)
    return cue
