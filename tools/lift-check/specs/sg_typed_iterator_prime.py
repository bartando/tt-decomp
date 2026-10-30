"""0x823DA070: skip non-sgNodes using the loaded type ID and low-byte result."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sg_typed_iterator import CALLS, inputs

FUNCTION = "sgTypedIterator::Prime"
ADDRESS = 0x823DA070
SOURCE = "src/scene/sg_scene_graph.cpp"
TRIALS = 1200
