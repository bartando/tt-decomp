"""0x82310FB8: page replacement callbacks, done lookup and signed transition."""
from liftcheck.spec import *
FUNCTION='pongLegalsContext::Update'
ADDRESS=0x82310FB8
SOURCE='src/game/match/pong_states.cpp'
TRIALS=600
EXTERNS={'g_loop_obj_ptr':0x825EAB30,'g_legalsDoneKey':0x8205DFB8}
S={}


def poll(c):c.write(c.r(3)+0x14,S['updated'].to_bytes(4,'big'))
def update(c):c.write(S['ctx']+0x14,S['group'].to_bytes(4,'big'))
def publish(c):c.write(0x825EAB30,S['newLoop'].to_bytes(4,'big'))

CALLS={
 'pongLegalsContext_InputPoll':model(poll,args=('r3',)),
 'page.vfn_2':model(update,args=('r3',)),
 'hudFlashBase_IsNetworkDirty':stub(ret=lambda c:S['acquired'],args=('r3',)),
 'hudFlashBase_GetPageGroup':stub(ret=lambda c:S['movie'],args=('r3',)),
 'swfFindPageGroupValue':stub(ret=lambda c:S['entry'],args=('r3','r4')),
 'swfValueToInteger':stub(ret=lambda c:S['done'],args=('r3',)),
 'hudFlashBase_PublishPageGroup':model(publish,args=('r3',)),
 'hsmContext_SetNextState':stub(ret='void',args=('r3','r4'))}


def inputs(t):
 r=t.rng
 ctx=t.alloc(0x20,'context')
 old=t.alloc(0x100,'oldPage')
 updated=t.alloc(0x100,'updatedPage')
 t.w32(updated,t.vtable('page',3))
 group=t.alloc(0x100,'group')
 t.w32(ctx+0x14,old if t.index%5 else 0)
 t.w32(t.sym('g_loop_obj_ptr'),t.alloc(0x40,'oldLoop'))
 S.update(ctx=ctx,updated=updated,group=group,newLoop=t.alloc(0x40,'newLoop'),
  acquired=r.choice([0,1,128,256,257]),movie=t.alloc(0xC0,'movie'),
  entry=t.alloc(8,'entry') if t.index%3 else 0,done=r.choice([0,1,2,0xFFFFFFFF,0x80000000,0x7FFFFFFF]))
 t.args(r3=ctx)
