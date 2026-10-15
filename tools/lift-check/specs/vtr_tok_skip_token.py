"""rage::fiAsciiTokenizer::SkipToken (0x822E6260), slot 11."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _vtr_tok import GET_TOKEN, SOURCE, name, tokenizer  # noqa: F401

FUNCTION = "rage::fiAsciiTokenizer::SkipToken"
ADDRESS = 0x822E6260

CALLS = {
    "tok.vfn_1": GET_TOKEN,
}


def inputs(t):
    obj = tokenizer(t)
    t.args(r3=obj)
