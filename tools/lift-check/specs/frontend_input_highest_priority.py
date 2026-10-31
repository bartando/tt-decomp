"""0x822ECD68: type/subtype filters, allowed types, signed priority and stable ties."""
from liftcheck.spec import *
FUNCTION='FrontendInput_FindHighestPriority'
ADDRESS=0x822ECD68
SOURCE='src/game/frontend_input.cpp'
TRIALS=800

def inputs(t):
 r=t.rng
 queue=t.alloc(0x93A0,'queue')
 count=r.choice([-1,0,1,2,4,7])
 t.w32(queue+0x9360,count)
 t.w32(queue+0x9398,r.choice([-1,0,1,3]))
 for i in range(3):t.w32(queue+0x9364+4*i,r.randrange(4))
 for i in range(max(0,count)):
  rec=queue+0x360+i*0x480
  t.w32(rec+4,r.choice([0,1,1,0xFFFFFFFF,0x80000000,0x7FFFFFFF]))
  t.w32(rec+8,r.randrange(4))
  t.w32(rec+0x2C,r.randrange(3))
 t.args(r3=queue,r4=t.alloc(0x480,'output'),r5=r.choice([-2,-1,0,1,3]),r6=r.choice([-1,0,1,2]))
