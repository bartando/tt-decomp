"""sgRMDrawable::RegisterFields (0x823D8F18): "Mesh" at +0x50, "Matrix" at +0x10."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "sgRMDrawable::RegisterFields"
ADDRESS = 0x823D8F18
SOURCE = "src/scene/sg_drawable.cpp"

EXTERNS = {"g_resourceFieldType": 0x825CAF88, "g_matrixFieldType": 0x825CAFA4}

CALLS = {
    "RegisterSerializationField": stub(ret="void"),
}


def inputs(t):
    t.args(r3=t.alloc(0x60, "node"))
