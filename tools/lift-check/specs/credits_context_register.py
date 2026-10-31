"""0x82309CA0: TLS allocation, constructor result and numeric version + 50."""
from specs._frontend_registration_inputs import *
FUNCTION='pongCreditsContext::RegisterWithCreditsRoll'
ADDRESS=0x82309CA0
SOURCE='src/game/match/pong_states.cpp'
TRIALS=400
EXTERNS={'g_creditsResourceVersion':0x82606520}
def inputs(t):make_inputs(t,0x82606520)
