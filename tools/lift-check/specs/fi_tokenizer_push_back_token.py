"""0x822E5310: token-length ABI, LIFO order, quotes, leading space and guards."""
from liftcheck.spec import *
FUNCTION = 'fiTokenizer_PushBackToken'
ADDRESS = 0x822E5310
SOURCE = 'src/rage/io/fiAsciiTokenizer.cpp'
TRIALS = 500
EXTERNS = {'strchr': 0x824321B0}
CALLS = {0x824321B0: run()}


def inputs(t):
    obj = t.alloc(0x300, 'tokenizerAndGuards') + 16
    value = t.pick((b'', b'alpha', b'a b', b'a\tb', b'"a b"', b'"', b' ', b'\t', b'\x80xy'))
    source = t.alloc(128, 'tokenAndGuards') + 16
    if t.index % 5 == 0:
        source = obj + 0x60
    t.put(source, value + b'\0')
    length = t.pick((len(value), len(value), 0, -2, len(value) + 2))
    t.args(r3=obj, r4=source, r5=length)
