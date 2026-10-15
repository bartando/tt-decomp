"""RegisterSerializationField (0x821A8F58): registry append under the main allocator.

The original passes the registry and 16 to 0x821A91E0, which reads neither; the
lift passes 16 in r3, so that call's arguments aren't compared."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "RegisterSerializationField"
ADDRESS = 0x821A8F58
SOURCE = "src/rage/data/par_xml_types.cpp"
EXTERNS = {"g_sda_base": 0x82600000, "atSingletonPool_AllocEntry": 0x821A91E0,
           "rage_strDuplicate": 0x820C29E0}

SDA = 0x82600000


def _entry(ctx):
    e = ctx.alloc(16)
    ctx.write(e, ctx.rng.getrandbits(32).to_bytes(4, "big"))
    return e


CALLS = {
    0x821A91E0: stub(ret=_entry, args=()),
    0x820C29E0: stub(),
    0x820C00C0: stub(ret="void"),
}


def inputs(t):
    rng = t.rng
    sda = t.alloc(0x20, "sda", fill="zero")
    tls = t.alloc(0x20, "tls")
    a, b = rng.getrandbits(32), rng.getrandbits(32)
    t.w32(tls + 4, a)
    t.w32(tls + 8, a if rng.random() < 0.5 else b)
    t.w32(tls + 0xC, rng.choice([0, 0, 1, 3]))
    t.w32(sda, tls)
    t.w32(SDA, sda)
    name = t.alloc(8, "name", fill=b"Quality\0")
    t.args(r3=t.u32(), r4=name, r5=t.u32(), r6=t.u32(), r7=0, r13=sda)
