"""rage::fiAsciiTokenizer::CheckVector4NoStageField (0x822E66B0), slot 23."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _vtr_tok import GET_TOKEN, SOURCE, name, tokenizer  # noqa: F401

FUNCTION = "rage::fiAsciiTokenizer::CheckVector4NoStageField"
ADDRESS = 0x822E66B0

CALLS = {
    "ph_58A8": stub(ret='void'),
    "tok.vfn_8": stub(ret='void', args=('r3','r4')),
}


def inputs(t):
    obj = tokenizer(t)
    nm = name(t)
    out = t.alloc(16, "out")
    t.args(r3=obj, r4=nm, r5=out)
