"""Three-axis rebuild: handedness, all lanes, degenerate axes and translation guard."""
from liftcheck.spec import *
FUNCTION="rage::mat33Orthonormalize"
ADDRESS=0x820C9220
SOURCE="src/rage/math/mat33_orthonormalize.cpp"
TRIALS=1400
# Scalar and VMX arithmetic can choose different NaN signs/payloads.
FTOL=1e-12


def inputs(t):
    r=t.rng
    p=t.alloc(96,"basis and guards",floats=[(16,16)])
    m=p+16
    vals=[0.,-0.,1.,-1.,1e-40,-1e-40,1e-20,-1e-20,float("nan"),float("inf"),-float("inf")]
    for i in range(16):
        t.wf32(m+i*4,r.choice(vals) if t.index%4==0 else r.uniform(-10,10))
    if t.index%8==1:
        for i in range(4): t.wf32(m+16+i*4,0)
    t.args(r3=m)
