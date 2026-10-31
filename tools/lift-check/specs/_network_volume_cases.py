from liftcheck.spec import *
SOURCE='src/rage/audio/xact_volume.cpp'
TRIALS=600
FTOL=0
CALLS={'rage::xactGroup_GetVolume':run(),'rage::xactSink_GetCombinedVolume':run(),
       'rage::xactSink_SetTargetVolume':run(),'rage::xactChild_UpdateVolume':run(),
       'msgMsgSink_3DC8_g':run(),
       'target.vfn_16':stub(ret='void',args=('r3','f1')),
       'group.vfn_6':stub(ret=lambda c:((c.r(4)&65535)-1)&0xFFFFFFFF,args=('r3','r4'))}
def scale(t): return t.rng.choice([0.0,1.0,-1.0,0.5,t.rng.uniform(-8,8)])
def make_group(t):
    owner=t.alloc(128,'group owner')
    group=t.alloc(128,'group')
    muted=t.alloc(32,'muted')
    solo=t.alloc(32,'solo')
    volumes=t.alloc(32,'volumes')
    t.w32(group,t.vtable('group',7))
    t.w32(group+0x70,muted)
    t.w32(group+0x6C,solo)
    t.w32(group+0x78,volumes)
    t.w32(group+0x74,t.rng.choice([0,0,0,1,t.u32()]))
    for i in range(8):
        t.w32(muted+i*4,t.rng.choice([0,0,0,0,1,t.u32()]))
        t.w32(solo+i*4,t.rng.choice([0,1,t.u32()]))
        t.wf32(volumes+i*4,scale(t))
    t.w32(owner+0x7C,t.rng.choice([0,group,group,group]))
    return owner
def make_root(t):
    root=t.alloc(128,'root sink')
    header=t.alloc(8,'header')
    session=t.alloc(32,'session')
    t.w16(header+1,t.rng.randrange(8))
    t.w32(root+0x1C,header)
    t.w32(root+0x20,make_group(t))
    t.w32(root+0x30,session)
    for offset in [8,0x58,0x70]: t.wf32(root+offset,scale(t))
    t.wf32(session+0x1C,scale(t))
    return root
def make_inner(t):
    inner=t.alloc(40,'inner sink')
    target=t.alloc(16,'volume target')
    t.w32(target,t.vtable('target',17))
    t.w32(inner+0x24,t.rng.choice([0,target,target]))
    return inner
def make_child(t):
    child=t.alloc(64,'child')
    t.w32(child+0x14,make_root(t))
    inner=make_inner(t)
    t.w32(child+0x18,t.rng.choice([0,inner,inner]))
    t.wf32(child+0x28,scale(t))
    t.wf32(child+0x38,scale(t))
    return child
def make_list(t):
    root=make_root(t)
    head=root+0x24
    previous=head
    for i in range(t.rng.randrange(5)):
        child=make_child(t)
        t.w32(previous+4,child)
        previous=child
    t.w32(previous+4,head)
    return root
