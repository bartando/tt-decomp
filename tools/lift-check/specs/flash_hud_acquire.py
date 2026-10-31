"""Flash semaphore and group access, including absent manager and noncanonical flag bytes."""
from specs._flash_hud_inputs import CALLS, EXTERNS, inputs
FUNCTION = "hudFlashBase_IsNetworkDirty"
ADDRESS = 0x822eb2a8
SOURCE = "src/rage/hud_page_group.cpp"
TRIALS = 1200
