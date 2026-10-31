from liftcheck.spec import *
FUNCTION = "localizedWideDuplicate"
ADDRESS = 0x82427E50
SOURCE = "src/rage/data/localized_text.cpp"
TRIALS = 400
CALLS = {"localizedWideLength": run(), "rage_Alloc": alloc()}
def inputs(t):
    text = t.alloc(130, 'text')
    for i in range(65): t.w16(text + i * 2, t.rng.randrange(1,65536))
    t.w16(text + t.rng.randrange(65) * 2, 0)
    t.args(r3=t.rng.choice([text,text,text,0]))
