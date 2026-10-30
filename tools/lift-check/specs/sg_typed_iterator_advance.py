"""0x823D9FD0: bounded pre-order successor, deep ancestor climb, then filtering."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sg_typed_iterator import CALLS, inputs

FUNCTION = "sgTypedIterator::Advance"
ADDRESS = 0x823D9FD0
SOURCE = "src/scene/sg_scene_graph.cpp"
TRIALS = 1200
