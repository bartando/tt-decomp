"""Full HUD lock, group selection, numeric-member insertion and lock release."""
from liftcheck.spec import *
from specs._swf_group_integrated_inputs import CALLS as SWF_CALLS, setup
FUNCTION = 'hudTrainingHUD_SetRemaining'
ADDRESS = 0x822FA7B8
SOURCE = 'src/game/drill/pong_drill.cpp'
TRIALS = 1000
CALLS = {**SWF_CALLS,
    'hudFlashBase_IsNetworkDirty': run(args=('r3',)),
    'hudFlashBase_GetPageGroup': run(args=('r3',)),
    'hudFlashBase_PublishPageGroup': run(args=('r3',)),
    'swfGetOrCreatePageGroupValue': run(args=('r3', 'r4')),
    0x8242C3B8: stub(ret=0, args=('r3', 'r4')),
    0x82566DC0: stub(ret=1, args=('r3', 'r4', 'r5')),
}


def inputs(t):
    group = setup(t)
    hud = t.alloc(0xC0, 'hud')
    t.w32(hud + 0x5C, group)
    loop = t.alloc(0x240, 'loop')
    manager = t.alloc(0x40, 'manager')
    t.w32(manager + 0x34, t.alloc(0x20, 'semaphore'))
    t.w32(loop + 0x22C, manager)
    t.w32(0x825EAB30, loop)
    t.w8(0x826065EB, 0)
    t.args(r3=hud, r4=t.u32())
