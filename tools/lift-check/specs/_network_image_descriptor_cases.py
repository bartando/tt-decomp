from liftcheck.spec import *
SOURCE='src/graphics/image_descriptor_queries.cpp'
TRIALS=600
def inputs(t):
    record=t.alloc(40,'image descriptor')
    t.w32(record+4,t.u32())
    t.w32(record+16,t.rng.choice([0,1,7,8,0x3FF8,0x4000,0xFFFFFFFF,t.u32()]))
    t.w32(record+20,t.rng.choice([0,1,2048,t.u32()]))
    t.args(r3=record)
