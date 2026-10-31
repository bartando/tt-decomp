"""0x8214C8F8: recovered canonical name for the existing skeleton rebuild lift.

Original composes are modeled; root calls can replace all skeleton metadata.
Later calls replace bone/matrix pointers and parent-table fields. Count/table
snapshots, fresh per-bone pointers, parent indices, strides and aligned row copy
(including overlapping root buffers) compare exactly.
"""
from liftcheck.spec import *

FUNCTION = 'LocomotionStateAnim_C8F8_g'
ADDRESS = 0x8214C8F8
SOURCE = 'src/game/creature/pong_creature.cpp'
TRIALS = 400


def u(c,a): return int.from_bytes(c.read(a,4),'big')
def w(c,a,v): c.write(a,(v & 0xFFFFFFFF).to_bytes(4,'big'))


def compose(c):
    script=u(c,c.r(4)+0x40)
    skeleton=u(c,script)
    state=u(c,script+36)
    a,b=c.read(c.r(4),64),c.read(c.r(5),64)
    c.write(c.r(3),bytes(x^y for x,y in zip(a,b)))
    version=1 if state%2==0 else 0
    w(c,skeleton+4,u(c,script+4+version*4))
    w(c,skeleton+12,u(c,script+12+version*4))
    w(c,skeleton+20,u(c,script+20+version*4))
    # Parent-table contents stay valid, but the field pointing at them changes.
    for i in range(2): w(c,u(c,script+4+i*4)+4,u(c,script+28+((state+i)%2)*4))
    w(c,script+36,state+1)


CALLS={0x820DEDC0:model(compose,args=('r3','r4','r5'))}


def inputs(t):
    rng=t.rng
    skeleton=t.alloc(0x20,'skeleton')
    script=t.alloc(48,'compose script')
    info=[t.alloc(16,'metadata') for _ in range(2)]
    bones=[t.alloc(8*80,'bone records') for _ in range(2)]
    matrices=[t.alloc(8*64,'matrices') for _ in range(2)]
    parents=[t.alloc(8*4,'parents') for _ in range(2)]
    helper=t.alloc(64,'root matrix')
    count=rng.choice((0,1,2,4,7))
    root=rng.choice((0,helper))
    if t.index%8==0:
        count,root=1,0
        matrices[0]=bones[0]+16
    for i in range(2):
        t.w32(info[i]+4,parents[i])
        t.w16(info[i]+12,count if i==0 else rng.choice((0,1,3,7)))
        for j in range(8):
            t.w32(parents[i]+j*4,rng.randrange(8))
            t.w32(bones[i]+j*80+64,script)
    t.w32(skeleton+4,info[0])
    t.w32(skeleton+8,root)
    t.w32(skeleton+12,bones[0])
    t.w32(skeleton+20,matrices[0])
    for i,value in enumerate((skeleton,*info,*bones,*matrices,*parents,0)):
        t.w32(script+i*4,value)
    t.args(r3=skeleton)
