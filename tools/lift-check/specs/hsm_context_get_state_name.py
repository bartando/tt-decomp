"""0x822228B8: low-byte gate and child-array reload across a virtual query."""
from liftcheck.spec import *
FUNCTION = 'hsmContext_GetStateName'
ADDRESS = 0x822228B8
SOURCE = 'src/rage/core/hsm.cpp'
TRIALS = 600
EXTERNS = {'g_hsmUnknownState': 0x8204DD08}
RESULT = 0
REPLACEMENT = 0
NAME = 0


def query(c):
 c.write(c.r(3)+8, REPLACEMENT.to_bytes(4,'big'))
 c.ret(r3=RESULT)


CALLS = {'manager.vfn_6': model(query, args=('r3',)),
         'state.vfn_13': stub(ret=lambda c:NAME, args=('r3',))}


def inputs(t):
 global RESULT, REPLACEMENT, NAME
 r=t.rng
 manager=t.alloc(0x18,'manager')
 t.w32(manager,t.vtable('manager',7))
 REPLACEMENT=t.alloc(32,'newStates')
 old=t.alloc(32,'oldStates')
 for array in [old,REPLACEMENT]:
  for i in range(8):
   state=t.alloc(8,'state')
   t.w32(state,t.vtable('state',14))
   t.w32(array+4*i,state)
 t.w32(manager+8,old)
 NAME=t.alloc(12,'name',fill=b'StateName\0')
 RESULT=r.choice([0,1,0x100,0x101,0xFF000000,0xFFFFFFFF])
 t.args(r3=manager,r4=r.randrange(8))
