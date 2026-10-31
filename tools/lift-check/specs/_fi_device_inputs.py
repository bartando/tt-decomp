"""Mount priority, byte flags, pointer-array reloads after device callbacks.
All prefix arrays, mount indices and per-mount device arrays are valid. Device
singletons are observed boundaries; this spec doesn't invent their methods.
"""
from liftcheck.spec import *
_tables=[]

def replace_table(c):
    c.write(0x8262F368,c.rng.choice(_tables).to_bytes(4,'big'))

def probe(c):
    replace_table(c)
    c.ret(r3=c.rng.choice([-1,-1,-2,0,1,0x12345678]))

def close(c):
    replace_table(c)
    c.ret()

CALLS = {'fiDevice_ComparePrefix':run(),
         'rage_DebugLog':stub(ret='void',args=('r3','r4'))}
for i in range(3):
    CALLS[f'device{i}.vfn_1']=model(probe,args=('r3','r4','r5'))
    CALLS[f'device{i}.vfn_6']=model(close,args=('r3','r4'))

def inputs(t):
    global _tables
    devices=[]
    for i in range(3):
        p=t.alloc(16,f'device{i}')
        t.w32(p,t.vtable(f'device{i}',slots=9))
        devices.append(p)
    _tables=[]
    count=t.rng.randrange(6)
    for k in range(2):
        mounts=t.alloc(0x114*6,f'mounts{k}')
        _tables.append(mounts)
        for i in range(6):
            mount=mounts+i*0x114
            prefix=t.rng.choice([b'',b'a/',b'A\\',b'abc/',b'abc/def/',b'x/'])
            t.put(mount,prefix+b'\0')
            t.w16(mount+0x106,t.rng.choice([0,0,1,0xffff]))
            t.w16(mount+0x108,len(prefix))
            array=t.alloc(12,'devicePointerArray')
            for j in range(3): t.w32(array+j*4,t.rng.choice(devices))
            t.w32(mount+0x10C,array)
            t.w16(mount+0x110,t.rng.randrange(4))
    t.w32(0x8262F368,_tables[0])
    t.w16(0x8262F36C,count)
    t.w32(0x825C481C,t.rng.choice([0]+devices))
    t.w8(0x826065EA,t.rng.choice([0,0,1,255]))
    path=t.rng.choice([b'memory:file',b'tcpip:file',b'cache:file',b'game:file',
                       b'abc/def/test',b'ABC\\def\\test',b'a/test',b'other',b''])
    t.args(r3=t.alloc(len(path)+1,'path',fill=path+b'\0'),
           r4=t.rng.choice([0,0,1,2,0x100,0x101,t.u32()]))

def prefix_input(t):
    def word():
        return bytes(t.rng.choice(b'abcXYZ/\\:012\0\xff') for _ in range(32))+b'\0'
    left=word()
    right=t.rng.choice([left,left.lower().replace(b'\\',b'/'),word()])
    t.args(r3=t.alloc(33,'left',fill=left),r4=t.alloc(33,'right',fill=right),r5=t.rng.randrange(33))
