"""0x82311098: four controller records, Flash lock checks, and quit value."""
from liftcheck.spec import *
FUNCTION = 'pongLegalsContext_InputPoll'
ADDRESS = 0x82311098
SOURCE = 'src/game/match/pong_states.cpp'
TRIALS = 600
EXTERNS = {'g_pPlayerDataTable':0x8271A31C,'g_loop_obj_ptr':0x825EAB30,
 'g_bNetworkDebugFlag':0x826065EB,'g_legalsQuitKey':0x8205DFB0,
 'g_flashSemaphoreError':0x8205AE98}
S={}


def pressed(c):
 c.write(S['ctx']+0x14,S['group'].to_bytes(4,'big'))
 c.ret(r3=int(c.r(3)==S['pressed']))


def acquire(c):
 c.write(S['group']+0x5C,S['movie'].to_bytes(4,'big'))
 c.ret(r3=S['acquired'])


def bind(c):
 c.ret(r3=S['entry'])


CALLS={'CheckButtonPressed':model(pressed,args=('r3',)),
 'hudFlashBase_IsNetworkDirty':model(acquire,args=('r3',)),
 'hudFlashBase_PublishPageGroup':stub(ret='void',args=('r3',)),
 'swfGetOrCreatePageGroupValue':model(bind,args=('r3','r4')),
 0x8240E6D0:stub(ret='void',args=('r3',))}


def inputs(t):
 r=t.rng
 ctx=t.alloc(0x20,'context')
 old=t.alloc(0x100,'oldGroup')
 group=t.alloc(0x100,'group')
 t.w32(ctx+0x14,old)
 t.w8(ctx+0x18,r.choice([0,0,0,1,128]))
 records=t.alloc(5*0x328,'records')
 buttons=[]
 for i in range(4):
  obj=t.alloc(0x40,f'buttons{i}')
  t.w32(records+(i+1)*0x328,obj)
  buttons.extend([obj+8,obj+16,obj+48])
 t.w32(t.sym('g_pPlayerDataTable'),records)
 loop=t.alloc(0x240,'loop')
 t.w32(loop+0x22C,r.choice([0,t.alloc(0x10,'manager')]))
 t.w32(t.sym('g_loop_obj_ptr'),loop)
 t.w8(t.sym('g_bNetworkDebugFlag'),r.choice([0,1,128]))
 S.update(ctx=ctx,group=group,movie=t.alloc(0xC0,'movie'),
  pressed=r.choice([0,0]+buttons),acquired=r.choice([0,1,128,256,257]),
  entry=t.alloc(8,'entry') if t.index%3 else 0)
 t.args(r3=ctx)
