"""0x8224EA28: forward timestep, reload joint-data pointer between stages."""
from liftcheck.spec import *
from specs.ph_articulated_set_timestep import inputs, stage

FUNCTION = "rage::phArticulatedCollider::PostIntegrate"
ADDRESS = 0x8224EA28
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 400
FTOL = 1e-99
CALLS = {
    "ph_IntegrateJointPositions": model(stage),
    "phArticulatedCollider_8450": model(stage),
    "phArticulatedCollider_F0E0": stub(ret="void"),
    "phArticulatedCollider_5D58": stub(ret="void"),
}
