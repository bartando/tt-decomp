"""0x82322470: defined iDone output, balanced lock and queued-input close callback."""
from liftcheck.spec import *
FUNCTION='DialogPageGroup_IsComplete'
ADDRESS=0x82322470
SOURCE='src/game/frontend_page_group.cpp'
TRIALS=600
EXTERNS={'g_dialogDoneKey':0x820627E4,'g_frontendInputQueue':0x8271A33C}
S={}

def done(c):
 assert c.in_stack(c.r(5))
 c.write(c.r(5),S['done'].to_bytes(4,'big'))
 c.ret(r3=1)

def input_event(c):
 assert c.in_stack(c.r(4))
 c.write(c.r(4),bytes(0x480))
 c.ret(r3=S['found'])

CALLS={'hudFlashBase_IsNetworkDirty':stub(ret=lambda c:S['acquired'],args=('r3',)),
 'hudFlashBase_GetPageGroup':stub(ret=lambda c:S['movie'],args=('r3',)),
 'swfGetPageGroupInteger':model(done,args=('r3','r4','r5')),
 'hudFlashBase_PublishPageGroup':stub(ret='void',args=('r3',)),
 'FrontendInput_FindHighestPriority':model(input_event,args=('r3','r4','r5','r6')),
 'dialog.vfn_5':stub(ret='void',args=('r3',))}

def inputs(t):
 r=t.rng
 group=t.alloc(0x100,'dialog')
 t.w32(group,t.vtable('dialog',6))
 t.w8(group+0x61,r.choice([0,1,128]))
 t.w32(t.sym('g_frontendInputQueue'),t.alloc(0x20,'queue'))
 S.update(acquired=r.choice([0,1,128,256,257]),movie=t.alloc(0xC0,'movie'),
  done=r.choice([0,1,2,0xFFFFFFFF,0x80000000,0x7FFFFFFF]),found=r.randrange(2))
 t.args(r3=group)
