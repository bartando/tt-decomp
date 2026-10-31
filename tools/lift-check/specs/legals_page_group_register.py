"""0x82309510: numeric resource version, lock and cached movie at +0xEC."""
from liftcheck.spec import *
FUNCTION='LegalsPageGroup_Register'
ADDRESS=0x82309510
SOURCE='src/game/frontend_page_group.cpp'
TRIALS=400
EXTERNS={'g_legalsResourceVersion':0x8260652C}
S={}
CALLS={'hudFlashBase_LoadPageGroup':stub(ret='void',args=('r3','r4')),
 'hudFlashBase_IsNetworkDirty':stub(ret=lambda c:S['acquired'],args=('r3',)),
 'hudFlashBase_GetPageGroup':stub(ret=lambda c:S['movie'],args=('r3',)),
 'hudFlashBase_PublishPageGroup':stub(ret='void',args=('r3',),deref={'r3':0xF0})}
def inputs(t):
 t.w32(t.sym('g_legalsResourceVersion'),t.rng.choice([0,1,0xFFFFFFFF,t.rng.getrandbits(32)]))
 S.update(acquired=t.rng.choice([0,1,128,256,257]),movie=t.alloc(0xC0,'movie') if t.index%3 else 0)
 t.args(r3=t.alloc(0xF0,'group'))
