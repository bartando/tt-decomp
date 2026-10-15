"""rage::fiAsciiTokenizer::vfn_0 (0x8210CAF8), slot 0: returns 0."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _vtr_tok import GET_TOKEN, SOURCE, name, tokenizer  # noqa: F401

FUNCTION = "rage::fiAsciiTokenizer::vfn_0"
ADDRESS = 0x8210CAF8


def inputs(t):
    obj = tokenizer(t)
    t.args(r3=obj)
