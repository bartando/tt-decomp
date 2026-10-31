from liftcheck.spec import *
from specs._localized_font_lifecycle_inputs import heap
S={}

def construct(c):
 c.write(S['versionSlot'],S['newVersion'].to_bytes(4,'big'))
 c.ret(r3=S['constructed'])

def load(c):c.write(S['context']+0x18,S['replacement'].to_bytes(4,'big'))

CALLS={0x8240E6D0:stub(ret='void',args=('r3',)),
 0x820C0038:stub(ret='void',args=()),
 'heap.vfn_1':stub(ret=lambda c:S['allocation'],args=('r3','r4','r5')),
 0x8231F4C0:model(construct,args=('r3',)),
 0x82321620:model(construct,args=('r3',)),
 0x822EADF8:model(load,args=('r3','r4'))}


def make_inputs(t,versionSlot):
 sda,thread,allocator=heap(t)
 r=t.rng
 context=t.alloc(0x24,'context')
 S.update(context=context,versionSlot=versionSlot,newVersion=r.choice([0,1,0xFFFFFFFF,r.getrandbits(32)]),
  allocation=t.alloc(0x600,'memory') if t.index%4 else 0,
  constructed=t.alloc(0x600,'constructed'),replacement=t.alloc(0x600,'replaced'))
 t.w32(versionSlot,r.getrandbits(32))
 t.w32(0x82606628,r.getrandbits(32))
 t.args(r3=context,r13=sda)
