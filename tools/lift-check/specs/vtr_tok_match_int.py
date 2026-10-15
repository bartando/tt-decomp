"""rage::fiAsciiTokenizer::MatchIntField (0x822E62A0), slot 12."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _vtr_tok import GET_TOKEN, SOURCE, name, tokenizer  # noqa: F401

FUNCTION = "rage::fiAsciiTokenizer::MatchIntField"
ADDRESS = 0x822E62A0

CALLS = {
    "tok.vfn_1": GET_TOKEN,
    "tok.vfn_4": stub(),
}


def inputs(t):
    obj = tokenizer(t)
    nm = name(t)
    t.args(r3=obj, r4=nm)
