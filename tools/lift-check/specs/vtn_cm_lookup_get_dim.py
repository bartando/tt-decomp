"""cmLookup::GetDim (0x8226D880): key = EvalFloat(+0xC); first entry i whose
threshold port (+0x14 + 16i) is >= key (ordered) yields GetDim(+0x1C + 16i),
else the default port +0x34."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "cmLookup::GetDim"
ADDRESS = 0x8226D880
SOURCE = "src/game/misc/cm_operators.cpp"
RET = None

CALLS = {
    "cmOperator_EvalFloat": stub(args=("r3",)),
    "cmNode_GetDim_stub": stub(args=("r3",)),
}


def inputs(t):
    obj = t.alloc(0x44, "cmLookup")
    t.args(r3=obj, r4=t.alloc(4, "out"))
