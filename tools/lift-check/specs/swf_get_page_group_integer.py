"""0x823F9808: preserve missing outputs and forward the complete integer word."""
from liftcheck.spec import *
FUNCTION='swfGetPageGroupInteger'
ADDRESS=0x823F9808
SOURCE='src/rage/swf_page_group.cpp'
TRIALS=500
VALUE=RESULT=0
CALLS={'swfFindPageGroupValue':stub(ret=lambda c:VALUE,args=('r3','r4')),
       'swfValueToInteger':stub(ret=lambda c:RESULT,args=('r3',))}

def inputs(t):
 global VALUE,RESULT
 VALUE=t.alloc(8,'value') if t.index%3 else 0
 RESULT=t.rng.getrandbits(32)
 t.args(r3=t.alloc(0xC0,'group'),r4=t.alloc(5,'key',fill=b'done\0'),r5=t.alloc(4,'output'))
