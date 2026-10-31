"""0x822E59C8: token matching and exact position restoration on pushback."""
from liftcheck.spec import *
from specs._tokenizer_token_inputs import inputs, CALLS, EXTERNS
FUNCTION = 'fiTokenizer_CheckTokenInsensitive'
ADDRESS = 0x822E59C8
SOURCE = 'src/rage/io/fiAsciiTokenizer.cpp'
TRIALS = 500
