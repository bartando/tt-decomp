"""0x8239BE30: signed fractional time, uint32 low-word conversions, fixed bound."""
from liftcheck.spec import *
FUNCTION = "networkFormatElapsedTime"
ADDRESS = 0x8239BE30
SOURCE = "src/game/network/network_timestamp.cpp"
TRIALS = 1000
EXTERNS = {"k_initRefreshRate": 0x825C4948}
def _format(ctx):
    pointer = ctx.r(6)
    sign = bytearray()
    while True:
        character = ctx.read(pointer + len(sign), 1)
        sign += character
        if character == b'\0': break
        assert len(sign) <= 1
    ctx.rec.derefs['sign string'] = (bytes(sign), None)
    ctx.ret(r3=ctx.rng.randrange(1 << 32))
CALLS = {"_snprintf": model(_format,args=('r3','r4','r5','r7','r8','r9'),deref={'r5':17})}
def inputs(t):
    destination = t.alloc(64,'time text')
    t.wf32(t.sym('k_initRefreshRate'),t.rng.choice([60.0,60.0,59.5,60.5]))
    if t.index == 0:
        t.wf32(t.sym('k_initRefreshRate'),59.5)
        t.args(r3=destination,r4=50,f1=170000007168.0)
        return
    if t.index % 3:
        value = t.rng.choice([-3600.75,-61.999,-60,-1,-0.0,0.0,0.999,1,59.999,60,60.125,3600.999,170000007168.0,250000015360.0,t.rng.uniform(-1e8,1e8)])
        t.args(r3=destination,r4=t.u32(),f1=value)
    else:
        import struct
        bits=t.rng.choice([0x7F800000,0xFF800000,0x7FC00000,0x5F000000,0xDF000000,t.u32()])
        value=struct.unpack('>f',bits.to_bytes(4,'big'))[0]
        t.args(r3=destination,r4=t.u32(),f1=value)
