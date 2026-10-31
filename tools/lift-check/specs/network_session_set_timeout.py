"""0x823ED4F8: context virtual, retail log, armed flag, wrapped deadline."""
from liftcheck.spec import *
from liftcheck.machine import STACK_LO, STACK_HI
FUNCTION = "rage::snSession_States::snSession_SetTimeout"
ADDRESS = 0x823ED4F8
SOURCE = "src/rage/network/session_state_helpers.cpp"
TRIALS = 600
def _log(ctx):
    assert STACK_LO <= ctx.r(3) < STACK_HI
    # Retail's diagnostic uses a scratch output pointer. Its bytes are never
    # consumed by the blr logger; normalize frame locations, retain format/args.
    ctx.rec.strings[0]=b'<scratch>'
    text=bytearray()
    while True:
        character=ctx.read(ctx.r(4)+len(text),1)
        text+=character
        if character==b'\0': break
    ctx.rec.derefs['format']=(bytes(text),None)
    ctx.ret()
CALLS = {'state.vfn_11': stub(ret=0x45000000),
         'nop_8240E6D0': model(_log,args=('r3','r5','r6'),deref={'r3':0})}
def inputs(t):
    state=t.alloc(24,'state')
    t.w32(state,t.vtable('state',12))
    context=t.map(0x45000000,0x1000,'context')
    t.w32(context+0x50,t.rng.choice([0,1,0xFFFFFFFF,0x7FFFFFFF,t.u32()]))
    t.args(r3=state,r4=t.rng.choice([0,1,10000,0xFFFFFFFF,0x80000000,t.u32()]))
