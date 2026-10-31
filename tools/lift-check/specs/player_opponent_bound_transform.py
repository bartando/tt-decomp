"""Four-byte pointer chain, late destination reload and VMX alignment."""
from liftcheck.spec import *
FUNCTION = "pongPlayer_4C08_g"
ADDRESS = 0x82194C08
SOURCE = "src/game/player/pong_gameplay_queries.cpp"
TRIALS = 512

def resolve(ctx):
    settings = ctx.r(3)
    ctx.ret(r3=int.from_bytes(ctx.read(settings, 4), "big"))

def matrix(ctx):
    capsule, output = ctx.r(3), ctx.r(4)
    ctx.write(output, ctx.read(capsule + 8, 64))
    player = int.from_bytes(ctx.read(capsule, 4), "big")
    ctx.write(player + 0x30, ctx.read(capsule + 4, 4))

CALLS = {
    "pongMatch_GetCharacterForSlot": model(resolve, args=("r3", "r4")),
    "phBoundCapsule_0880_g": model(matrix, args=("r3", "r4", "r5")),
}

def inputs(t):
    player = t.alloc(0x1d0, "player")
    opponent = t.alloc(0xc0, "opponent")
    character = t.alloc(0x20, "character")
    record = t.alloc(0x30, "record")
    owner = t.alloc(0x150, "bound owner")
    capsule = t.alloc(80, "capsule")
    settings = t.alloc(4, "settings")
    destination = t.alloc(0x80, "destination")
    t.w32(player + 0x1c4, opponent if t.index % 4 else 0)
    t.w32(opponent + 0xbc, character)
    t.w32(record + 0x2c, owner)
    t.w32(owner + 0x144, capsule)
    t.w32(character + 8, t.rng.getrandbits(32))
    t.w32(character + 0x1c, t.alloc(8, "sampling state"))
    t.w32(settings, record)
    t.w32(0x825eab28, settings)
    t.w32(player + 0x30, t.alloc(0x80, "old destination"))
    t.w32(capsule, player)
    t.w32(capsule + 4, destination + t.rng.randrange(16))
    t.args(r3=player)
