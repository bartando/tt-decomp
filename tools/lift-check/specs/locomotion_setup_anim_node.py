"""0x820E10D8: clip evaluation ABI, phase fallback and full transform pair.

Evaluate replaces the frame pointer and fallback fields; pair fetching fills all
32 bytes and matrix construction can modify the translation row before its copy.
The original consumes undefined scratch on missing channels; model only complete
pairs. All output bytes/calls compare, including NaN time forwarding and VMX align.
"""
import struct
from liftcheck.spec import *

FUNCTION = 'LocomotionStateAnim_10D8'
ADDRESS = 0x820E10D8
SOURCE = 'src/game/creature/pong_creature.cpp'
TRIALS = 400
EXTERNS = {'g_floatZero': 0x8202D110}


def u(c,a): return int.from_bytes(c.read(a,4),'big')


def evaluate(c):
    clip = c.r(3)
    obj, replacement = struct.unpack('>II',c.read(clip + 0x20,8))
    c.write(obj + 0x1C,struct.pack('>I',replacement))
    c.ret(r3=0)


def pair(c):
    c.write(c.r(7), c.read(c.r(3) + 0x20,32))
    c.ret(r3=1)


def matrix(c):
    # Stand in for AD30, preserving its output pointer return and live scratch.
    q = c.read(c.r(4),16)
    c.write(c.r(3), q*3)
    c.write(c.r(4)+16,bytes.fromhex('40e00000410000004110000041200000'))
    c.ret(r3=c.r(3))


CALLS = {
    0x822488E0: model(evaluate,args=('r3','r4','r5','r6','r7','f1')),
    0x8224C358: model(pair,args=('r3','r4','r5','r6')),
    0x8223AD30: model(matrix,args=('r3','r4'),deref={'r4':16}),
}


def inputs(t):
    rng=t.rng
    obj=t.alloc(0x160,'state')
    clips=[t.alloc(0x40,'clip') for _ in range(2)]
    frames=[t.alloc(0x50,'frame') for _ in range(2)]
    dst=t.alloc(112,'matrix and guards')+16+rng.randrange(4)*4
    for clip in clips:
        t.w32(clip+0x20,obj)
        t.w32(clip+0x24,frames[1])
    for frame in frames: t.floats(frame+0x20,8,-4,4)
    t.w32(obj+0x140,clips[0])
    t.w32(obj+0x1C,frames[0])
    t.wf32(obj+0xB8,rng.uniform(-5,5))
    time=rng.choice((0.,-0.,1.,-1.,float('nan'),rng.uniform(-2,2)))
    t.args(r3=obj,r4=dst,r5=rng.getrandbits(32),r6=0 if t.index%2 else clips[1],f1=time)
