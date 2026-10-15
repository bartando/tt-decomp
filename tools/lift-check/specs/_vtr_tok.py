"""Shared pieces for the fiAsciiTokenizer slot specs (not a spec itself).

The tokenizer gets a fake vtable "tok", so every virtual call shows up as
tok.vfn_<slot> and a wrong slot number is a call-trace mismatch.
"""
from liftcheck.spec import stub

SOURCE = "src/rage/io/fiAsciiTokenizer.cpp"

# Tokens are 0 or >= 2 chars: lift-check compares 1-char strings as pointers.
TOKENS = [b"", b"-12", b"345", b"abc", b".5", b"7.25", b"-0.5", b"x1", b"09"]


def _get_token(ctx):
    tok = ctx.rng.choice(TOKENS)
    ctx.write(ctx.r(4), tok + b"\0")
    return len(tok)


# slot 1 GetToken(char* out, int outSize): writes a token, returns its length.
GET_TOKEN = stub(ret=_get_token, args=("r3", "r5"))


def tokenizer(t):
    obj = t.alloc(0xB0, "tok")
    t.w32(obj, t.vtable("tok", slots=40))
    return obj


def name(t):
    return t.alloc(16, "name", fill=b"FieldName\0".ljust(16, b"\0"))
