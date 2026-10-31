"""Trail point transform: all lanes, overlapping source and VMX denormals."""
from liftcheck.spec import *
FUNCTION='rage::mat34TransformPointInPlace'
ADDRESS=0x820D2038
SOURCE='src/rage/math/mat34_transform.cpp'
TRIALS=1200
FTOL=1e-12 # NaN payload/sign choices may differ between scalar and VMX arithmetic.

def inputs(t):
    r=t.rng
    matrix=t.alloc(96,'matrix',floats=[(16,16)])+16
    point=t.alloc(48,'point',floats=[(16,4)])+16
    vals=[0.,-0.,1e-40,-1e-40,1e-20,-1.,1.,float('nan'),float('inf'),-float('inf')]
    for i in range(16):t.wf32(matrix+4*i,r.choice(vals) if t.index%3==0 else r.uniform(-10,10))
    for i in range(4):t.wf32(point+4*i,r.choice(vals) if t.index%3==0 else r.uniform(-10,10))
    if t.index%5==1:point=matrix+r.choice([0,16,32,48])
    t.args(r3=matrix,r4=point)
