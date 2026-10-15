"""rage::fiAsciiTokenizer::WriteBlockOpen (0x822E67A0), slot 26: depth tabs, '{', CR, LF, depth++."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _vtr_tok import GET_TOKEN, SOURCE, name, tokenizer  # noqa: F401

FUNCTION = "rage::fiAsciiTokenizer::WriteBlockOpen"
ADDRESS = 0x822E67A0

CALLS = {
    "fiAsciiTokenizer_51F0": stub(ret='void'),
}


def inputs(t):
    obj = tokenizer(t)
    t.w32(obj + 0xA0, t.rng.randrange(0, 5))
    t.args(r3=obj)
