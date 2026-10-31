"""0x8230C808: load the actual group and reload it before publishing the global."""
from specs._frontend_registration_inputs import *
FUNCTION='pongDialogContext::Register'
ADDRESS=0x8230C808
SOURCE='src/game/match/pong_states.cpp'
TRIALS=400
EXTERNS={'g_dialogResourceVersion':0x82606514,'g_dialogPageGroup':0x82606628}
def inputs(t):make_inputs(t,0x82606514)
