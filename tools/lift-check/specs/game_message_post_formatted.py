"""0x8225E480: raw-word varargs, padded strings, ignored format characters."""
from specs.game_message_post import CALLS
from liftcheck.spec import *
FUNCTION='PostGameMessageFmt'
ADDRESS=0x8225E480
SOURCE='src/game/game_message.cpp'
TRIALS=800

def inputs(t):
 r=t.rng
 fmt=r.choice(['','i','fff','s','ssi','fi','isf','?i!s','f?i','sssss'])
 values=[]
 for tag in fmt:
  if tag in 'if':values.append(r.getrandbits(32))
  elif tag=='s':
   length=1020 if t.index%7==0 and not values else r.choice([0,1,2,3,4,7,12,60])
   data=bytes(r.randrange(1,256) for _ in range(length))+b'\0'+r.randbytes(4)
   values.append(t.alloc(len(data),'text',fill=data))
 t.w32(0x825F3860,r.randrange(128))
 t.w8(0x825EE297,r.randrange(2))
 t.put(0x825F3AA8,r.randbytes(8192))
 args=dict(r3=r.getrandbits(32),r4=r.choice([0,1,64,65,128,192,256,0xFFFFFFFF]),
  r5=t.alloc(len(fmt)+1,'format',fill=fmt.encode()+b'\0'))
 for i,value in enumerate(values):args[f'r{6+i}']=value
 t.args(**args)
