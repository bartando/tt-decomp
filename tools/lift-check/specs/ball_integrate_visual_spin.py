"""Visual spin integration with the original axis rotation, composition and basis repair."""
from liftcheck.spec import *
FUNCTION="BallNode_IntegrateVisualSpin"
ADDRESS=0x82282240
SOURCE="src/game/ball/ball_visual_spin.cpp"
TRIALS=1200
FTOL=1e-12
CALLS={
    "crt_sqrt":run(),
    "rage::mat33RotationNormalizedAxis":run(),
    "rage::mat33ComposeInPlace":run(),
    "rage::mat33Orthonormalize":run(),
    "crt_cos":run(),
    "crt_sin":run(),
}


def inputs(t):
    r=t.rng
    node=t.alloc(0x150,"ball node",floats=[(0x90,1)])
    matrix=t.alloc(96,"matrix and guards",floats=[(16,16)])+16
    t.floats(matrix,16,-2,2)
    spin=t.alloc(16,"spin",floats=[(0,4)])
    modes=[0.,-0.,1e-40,-1e-40,1e-20,-1e-20,1e-18,1.,-1.,10.,float("nan"),float("inf")]
    for lane in range(4):t.wf32(spin+4*lane,r.choice(modes) if t.index%3==0 else r.uniform(-100,100))
    if t.index%5==1:spin=matrix+16
    t.wf32(node+0x90,r.choice([0.,-1.,0.01,0.5,1.,2.,float("nan")]))
    dt=r.choice([0.,0.001,1/60,1/30,1.])
    t.args(r3=node,r4=r.getrandbits(32),r5=spin,r6=matrix,f1=dt)
