"""rage::fiAsciiTokenizer::GetVector4 (0x822E6190), slot 6."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _vtr_tok import GET_TOKEN, SOURCE, name, tokenizer  # noqa: F401

FUNCTION = "rage::fiAsciiTokenizer::GetVector4"
ADDRESS = 0x822E6190

CALLS = {
    "tok.vfn_5": stub(),
}


def inputs(t):
    obj = tokenizer(t)
    out = t.alloc(16, "out")
    t.args(r3=obj, r4=out)
