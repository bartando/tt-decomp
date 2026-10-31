"""0x82188130: only flag one unlocks; every path clears the flag."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from game_message_guard_enter import *

FUNCTION = "GameMessageGuard_Leave"
ADDRESS = 0x82188130
CALLS = {0x82585DFC: stub(ret="void", args=("r3",))}
