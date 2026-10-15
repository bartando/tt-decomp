"""rage::fiAsciiTokenizer::MatchFloatField (0x822E6300), slot 13."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _vtr_tok import GET_TOKEN, SOURCE, name, tokenizer  # noqa: F401

FUNCTION = "rage::fiAsciiTokenizer::MatchFloatField"
ADDRESS = 0x822E6300

CALLS = {
    "tok.vfn_1": GET_TOKEN,
    "tok.vfn_5": stub(),
}


def inputs(t):
    obj = tokenizer(t)
    nm = name(t)
    t.args(r3=obj, r4=nm)
