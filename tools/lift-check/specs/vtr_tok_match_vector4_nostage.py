"""rage::fiAsciiTokenizer::MatchVector4NoStageField (0x822E6440), slot 16."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _vtr_tok import GET_TOKEN, SOURCE, name, tokenizer  # noqa: F401

FUNCTION = "rage::fiAsciiTokenizer::MatchVector4NoStageField"
ADDRESS = 0x822E6440

CALLS = {
    "tok.vfn_1": GET_TOKEN,
    "tok.vfn_8": stub(ret='void', args=('r3','r4')),
}


def inputs(t):
    obj = tokenizer(t)
    nm = name(t)
    out = t.alloc(16, "out")
    t.args(r3=obj, r4=nm, r5=out)
