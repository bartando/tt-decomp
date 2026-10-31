"""Original command helper with state-changing boundary models; compare all writes."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _grc_command_helpers_inputs import inputs as common, CALLS, HOST
FUNCTION = 'rage_A4E0'
ADDRESS = 0x8235a4e0
SOURCE = 'src/graphics/grc_command_stream.cpp'
TRIALS = 650


def inputs(t):
    common(t, 'query')
