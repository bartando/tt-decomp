from liftcheck.spec import *
FUNCTION = "localizedWideLength"
ADDRESS = 0x82433748
SOURCE = "src/rage/data/localized_text.cpp"
TRIALS = 400
def inputs(t):
    text = t.alloc(260, 'text')
    for i in range(130): t.w16(text + i * 2, t.rng.randrange(1,65536))
    t.w16(text + t.rng.randrange(130) * 2, 0)
    t.args(r3=text)
