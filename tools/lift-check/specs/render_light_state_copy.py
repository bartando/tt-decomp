"""Full light-state copy reuses the existing eight-light lift, preserving padding."""
from liftcheck.spec import *
from specs.pong_light_state_copy_lights import inputs

FUNCTION = "game_E0A8"
ADDRESS = 0x8213E0A8
SOURCE = "src/game/pong_render.cpp"
TRIALS = 1200
# Execute the actual callee on both sides; its own spec checks the existing lift.
CALLS = {"pongLightState_CopyLights": run()}
