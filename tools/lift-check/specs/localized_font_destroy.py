"""Resource cleanup may replace the head/name; unlink and free owned capacities."""
from specs._localized_font_lifecycle_inputs import DESTROY_CALLS as CALLS, destroy_inputs as inputs

FUNCTION = "localizedFontDestroy"
ADDRESS = 0x82409490
SOURCE = "src/rage/localized_font_lifecycle.cpp"
TRIALS = 500
