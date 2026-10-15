"""phObject_CreateStreamContext (XMV, 0x8248AD78): work buffer, then
rage_A518's context; frees the buffer and returns null if either fails. Both
callees are stubs whose out-params get random data and whose HRESULTs are
random (so both signs come up)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "phObject_CreateStreamContext"
ADDRESS = 0x8248AD78
SOURCE = "src/physics/ph_physics.cpp"
EXTERNS = {"phObject_AllocateWorkBuffer": 0x82491980, "phObject_1F70": 0x82491F70,
           "rage_A518": 0x8248A518}


def hresult(ctx):
    return ctx.rng.choice([0, 1, 0x80004005, 0x8007000E])


CALLS = {
    0x82491980: stub(ret=hresult, out={"r3": 4}),
    0x8248A518: stub(ret=hresult, out={"r3": 4}, args=("r4", "r5")),
    0x82491F70: stub(),
}


def inputs(t):
    t.args(r3=t.alloc(0x40, "xmv"))
