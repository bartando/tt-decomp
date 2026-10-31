"""0x822E5908: token matching and exact position restoration on pushback."""
from liftcheck.spec import *
from specs._tokenizer_token_inputs import inputs, CALLS, EXTERNS
FUNCTION = 'fiTokenizer_CheckToken'
ADDRESS = 0x822E5908
SOURCE = 'src/rage/io/fiAsciiTokenizer.cpp'
TRIALS = 500
