"""gmPracticeTarget::LoadData (slot 1, 0x82112DF8): reads "$/fx" fx_target.fx,
fx_target2.fx and practice_targets.fx.

The tokenizer is scripted: each trial draws a practice_targets file as a token
list, and the tokenizer calls (CheckToken 0x822E5908, GetInt 0x822E5E88,
GetFloat 0x822E5F08, slot 1 GetToken 0x822E5550, and the Set loader 0x82113F20)
consume it, each side from its own cursor. Every call that gets the tokenizer
checks the fields the inlined constructor set.
"""
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmPracticeTarget::LoadData"
ADDRESS = 0x82112DF8
SOURCE = "src/game/match/pong_match.cpp"

EXTERNS = {
    "fiAssetManager_PushFolder": 0x822E2E60,
    "fiAssetManager_Open": 0x822E3040,
    "fiStream_Close": 0x822E3B38,
    "fiTokenizer_CheckToken": 0x822E5908,
    "fiTokenizer_GetInt": 0x822E5E88,
    "fiTokenizer_GetFloat": 0x822E5F08,
    "gmPracticeTargetFx_Load": 0x82113DF8,
    "gmPracticeTargetSet_Load": 0x82113F20,
    "gmPracticeTargetWordArray_Init": 0x821B2A58,
    "xe_EC88": 0x820DEC88,
    "g_fiAssetManager": 0x825D0080,
    "g_fiTokenizer_vtable": 0x8205A594,
    "g_practiceTargetNumSets": 0x826063AC,
    "g_practiceTargetDefaultColor": 0x825CA198,
    "g_practiceTargetHitColor": 0x825CA19C,
}

_st = {"script": [], "orig": 0, "lift": 0, "streams": {}}


def _cstr(ctx, p):
    out = b""
    while len(out) < 64:
        c = ctx.read(p + len(out), 1)
        if c == b"\0":
            break
        out += c
    return out.decode("latin-1")


def _check_tokenizer(ctx, tk, name=None):
    """The fields fiTokenizer_Init writes (vtable 0x8205A594, 1, stream, 0x20, 2, 0, "", 0, 0)."""
    w = lambda o: struct.unpack(">I", ctx.read(tk + o, 4))[0]  # noqa: E731
    got = (w(0x00), w(0x08), w(0x10), w(0x14), w(0x18), ctx.read(tk + 0x1C, 1)[0], w(0x9C), w(0xA0))
    assert got == (0x8205A594, 1, 0x20, 2, 0, 0, 0, 0), f"tokenizer fields {[hex(v) for v in got]}"
    tk_name = _cstr(ctx, w(0x04))
    stream = w(0x0C)
    assert _st["streams"].get(stream) == tk_name, f"tokenizer {tk_name!r} on stream {stream:#x}"
    if name is not None:
        assert tk_name == name, f"tokenizer name {tk_name!r}"


def _head(ctx):
    k = _st[ctx.side]
    s = _st["script"]
    return s[k] if k < len(s) else ("eof", None)


def _next(ctx):
    _st[ctx.side] += 1


def _check_token(ctx):
    _check_tokenizer(ctx, ctx.r(3), "practice_targets")
    want = _cstr(ctx, ctx.r(4))
    kind, v = _head(ctx)
    hit = kind == "tok" and v == want
    if hit and ctx.r(5) & 0xFF:
        _next(ctx)
    ctx.ret(r3=1 if hit else 0)


def _get_int(ctx):
    _check_tokenizer(ctx, ctx.r(3), "practice_targets")
    kind, v = _head(ctx)
    _next(ctx)
    ctx.ret(r3=v if kind == "int" else 0)


def _get_float(ctx):
    _check_tokenizer(ctx, ctx.r(3), "practice_targets")
    kind, v = _head(ctx)
    _next(ctx)
    ctx.ret(f1=v if kind == "float" else 0.0)


def _get_token(ctx):
    _check_tokenizer(ctx, ctx.r(3), "practice_targets")
    buf, size = ctx.r(4), ctx.r(5)
    assert size == 0x40 and ctx.read(buf, 1) == b"\0", "GetToken buffer"
    kind, v = _head(ctx)
    _next(ctx)
    word = (v if kind == "word" else "").encode()[: size - 1] + b"\0"
    ctx.write(buf, word)
    return "void"


def _load_set(ctx):
    _check_tokenizer(ctx, ctx.r(4), "practice_targets")
    kind, v = _head(ctx)
    _next(ctx)
    n = v if kind == "set" else 0
    ctx.write(ctx.r(3), struct.pack(">iI", n, 0x7A000000 + 0x44 * (n & 0xFF)))


def _load_fx(ctx):
    _check_tokenizer(ctx, ctx.r(4))


def _open(ctx):
    name = _cstr(ctx, ctx.r(4))
    stream = 0 if ctx.rng.random() < 0.15 else 0x7B000000 + (ctx.rng.getrandbits(12) << 4)
    if stream:
        _st["streams"][stream] = name
    return stream


def _new(ctx):
    n = ctx.r(3)
    ctx.ret(r3=0 if n > 0x10000 else ctx.alloc(n))


CALLS = {
    0x822E2E60: stub(ret="void"),                         # push folder
    0x822E3040: stub(ret=_open),                          # open name.ext
    0x822E3B38: stub(ret="void"),                         # close
    0x82113DF8: model(_load_fx),
    0x822E5908: model(_check_token),
    0x822E5E88: model(_get_int),
    0x822E5F08: model(_get_float),
    # tokenizer slot 1: an indirect call without a declaration, so name what to
    # compare (r3/r4 are stack addresses that differ between the two frames)
    0x822E5550: stub(ret=_get_token, args=("r5",), auto_out=False),
    0x82113F20: model(_load_set),
    0x820DEC88: model(_new),                              # operator new[]
    0x821B2A58: stub(ret="void"),
}


def _f32(x):
    return struct.unpack(">f", struct.pack(">f", x))[0]


def _script(rng):
    s = []
    junk = lambda: rng.random() < 0.08  # noqa: E731
    if rng.random() < 0.9:
        s.append(("tok", "NumSets"))
    n = rng.choice([0, 1, 2, 3, 4, 6, -1, -3])
    s.append(("int", n))
    for name in ("TargetDefaultColor", "TargetHitColor"):
        if junk():
            s.append(("word", "junk"))
        if rng.random() < 0.85:
            s.append(("tok", name))
            for _ in range(4):
                s.append(("float", _f32(rng.choice([rng.uniform(0, 1), rng.uniform(0, 1), 1.0, 0.0,
                                                      rng.uniform(-0.5, 1.5)]))))
    for _ in range(max(n, 0) + rng.choice([0, 0, 1])):
        if rng.random() < 0.85:
            s.append(("tok", "Set"))
            s.append(("word", rng.choice(["{", "Easy", "Hard"])))
            s.append(("set", rng.choice([0, 1, 3, 8, 12, rng.randrange(40)])))
            s.append(("word", "}"))
        elif junk():
            s.append(("word", "junk"))
    return s


def inputs(t):
    rng = t.rng
    _st.update(script=_script(rng), orig=0, lift=0, streams={})
    target = t.alloc(0x70, "target", ctype="gmPracticeTarget")
    t.w32(target + 0x18, t.alloc(0x14, "wordArray"))
    t.w32(0x825D0080 + 0x600, rng.randrange(1, 6))     # folder depth
    t.args(r3=target)
