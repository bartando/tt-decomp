"""Slot 20 preserves the resource result and uses the fallback texture directly."""
from liftcheck.spec import *
FUNCTION = 'rage::grcTextureReferenceBase::ForwardSlot20'
ADDRESS = 0x8215D510
SOURCE = 'src/graphics/texture_reference.cpp'
TRIALS = 800
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _texture_reference_inputs import inputs, CALLS
