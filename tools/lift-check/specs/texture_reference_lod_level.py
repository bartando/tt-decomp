"""LOD forwarding selects slot 12, preserves full argument bits and accepts null."""
from liftcheck.spec import *
from specs._texture_reference_inputs import inputs, get_texture

FUNCTION = "rage::grcTextureReferenceBase::ForwardSlot16"
ADDRESS = 0x8215D940
SOURCE = "src/graphics/texture_reference.cpp"
TRIALS = 600
CALLS = {
    "reference.vfn_12": model(get_texture, args=("r3",)),
    "texture.vfn_16": stub(ret="void", args=("r3", "r4")),
}
