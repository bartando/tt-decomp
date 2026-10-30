"""0x820F0AA0: shader buckets containing linked lists of model/geometry draws.

No callees: compare every write, including existing head/tail links, adjacent
sentinels and 16-bit count/index truncation. r7 is an unused caller argument.
"""
from liftcheck.spec import *

FUNCTION = "rage::grmDrawQueue_AddGeometry"
ADDRESS = 0x820F0AA0
SOURCE = "src/rage/rage_grm.cpp"
TRIALS = 1000


def inputs(t):
    r = t.rng
    new_shader = r.choice((False, True))
    shader_count = r.randrange(1, 33)
    draw_count = r.randrange(1, 65)
    # Exercise halfword rollover without making every trial a half-megabyte.
    if r.randrange(32) == 0:
        shader_count = r.choice((0, 255, 256, 65534, 65535))
    if r.randrange(32) == 0:
        draw_count = r.choice((0, 255, 256, 65534, 65535))
    shader_index = 0 if new_shader else r.randrange(1, 33)
    buckets = t.alloc((max(shader_count, shader_index) + 2) * 8, "shaderBuckets")
    draws = t.alloc((draw_count + 2) * 8, "drawEntries")
    queue = t.alloc(0x18, "queue")
    shader = t.alloc(0x20, "shader")
    model = t.alloc(0x20, "model")
    t.w32(queue, buckets)
    t.w16(queue + 4, shader_count)
    t.w32(queue + 8, draws)
    t.w16(queue + 12, draw_count)
    t.w32(shader + 8, shader_index)
    if not new_shader:
        bucket = buckets + shader_index * 8
        # Empty bucket, first append, and append after a preexisting tail.
        head = r.choice((0, r.randrange(1, max(draw_count, 2))))
        tail = r.choice((0, r.randrange(1, max(draw_count, 2))))
        t.w16(bucket + 4, head)
        t.w16(bucket + 6, tail)
    geometry_index = r.choice((0, 1, 65535, 65536, 0x80000000, 0xFFFFFFFF, t.u32()))
    t.args(r3=queue, r4=shader, r5=model, r6=geometry_index, r7=t.u32())
