"""Parallel texture/effect arrays, reference wrapping, and tracked side blocks."""
from specs._localized_font_lifecycle_inputs import CLEAR_CALLS as CALLS, clear_inputs as inputs

FUNCTION = "localizedFontClearResources"
ADDRESS = 0x82409F08
SOURCE = "src/rage/localized_font_lifecycle.cpp"
TRIALS = 500
# Marker scan also sees unrelated class methods named Release.
EXTERNS = {"rage::Release(rage::grcTexture*)": 0x820C2E18}
