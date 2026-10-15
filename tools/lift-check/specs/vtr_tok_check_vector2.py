"""rage::fiAsciiTokenizer::CheckVector2Field (0x822E6610), slot 25."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _vtr_tok import GET_TOKEN, SOURCE, name, tokenizer  # noqa: F401

FUNCTION = "rage::fiAsciiTokenizer::CheckVector2Field"
ADDRESS = 0x822E6610

CALLS = {
    "ph_58A8": stub(ret='void'),
    "tok.vfn_10": stub(ret='void', args=('r3','r4')),
}


def inputs(t):
    obj = tokenizer(t)
    nm = name(t)
    out = t.alloc(16, "out")
    t.args(r3=obj, r4=nm, r5=out)
