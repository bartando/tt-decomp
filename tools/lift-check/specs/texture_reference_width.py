"""Texture reference virtual forwarding, including the unbound path."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *
from _texture_reference_inputs import inputs, _state, get_texture
FUNCTION = 'rage::grcTextureReferenceBase::ForwardSlot8'
ADDRESS = 0x8215d720
SOURCE = 'src/graphics/texture_reference.cpp'
TRIALS = 800
CALLS = {
    'reference.vfn_11': model(get_texture, args=('r3',)),
    'texture.vfn_8': model(lambda ctx: ctx.ret(r3=_state['resource']), args=('r3',)),
}
