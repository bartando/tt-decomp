import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _player_pose_easing_common import *

FUNCTION = "ph_ClampAndSin"
SOURCE = "src/physics/ph_physics.cpp"
ADDRESS = 0x820CB6A0
