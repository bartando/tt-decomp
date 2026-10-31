"""0x8230C8A8: reload page and transition index after their callbacks."""
from liftcheck.spec import *
FUNCTION='pongDialogContext::Update'
ADDRESS=0x8230C8A8
SOURCE='src/game/match/pong_states.cpp'
TRIALS=500
EXTERNS={'g_loop_obj_ptr':0x825EAB30}
S={}

def update(c):c.write(S['ctx']+0x18,S['group'].to_bytes(4,'big'))
def complete(c):
 c.write(S['ctx']+0x1C,S['next'].to_bytes(4,'big'))
 c.ret(r3=S['complete'])
CALLS={'page.vfn_2':model(update,args=('r3',)),
 'DialogPageGroup_IsComplete':model(complete,args=('r3',)),
 'hsmContext_SetNextState':stub(ret='void',args=('r3','r4'))}

def inputs(t):
 r=t.rng
 ctx=t.alloc(0x24,'context')
 page=t.alloc(0x100,'page')
 t.w32(page,t.vtable('page',3))
 t.w32(ctx+0x18,page if t.index%5 else 0)
 t.w32(t.sym('g_loop_obj_ptr'),t.alloc(0x20,'loop'))
 S.update(ctx=ctx,group=t.alloc(0x100,'newGroup'),next=r.getrandbits(32),complete=r.choice([0,1,128,256,257]))
 t.args(r3=ctx)
