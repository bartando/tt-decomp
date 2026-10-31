"""Asset path layout, bounded output, parent collapse and basename diagnostics.
Non-null valid names, a valid root/folder index and writable output byte are
required even with capacity <= 0 (as in the original). No ignored bytes.
"""
from liftcheck.spec import *
EXTERNS = {'strchr':0x824321B0, 'strrchr':0x82430EA0}
CALLS = {'rage_strcat_bounded': run(), 'fiPath_RemoveParentDir': run(),
         'fiPath_AppendName': run(), '_stricmp': run(transparent=True),
         'strchr': run(transparent=True), 'strrchr':run(transparent=True),
         'rage_DebugLog': stub(ret='void', args=('r3','r4'))}


def text(t, s, label):
    b = s.encode() + b'\0'
    return t.alloc(len(b) + 16, label, fill=b + bytes(16))


def append_input(t):
    # Large storage leaves the literal basename replacement safe at every length.
    out = t.alloc(512, 'outputAndGuards', fill=bytes(512))
    prefix = t.rng.choice(['', '/', 'root/', 'a\\b/', '//server//', 'folder/'])
    t.put(out, prefix.encode() + b'\0')
    name = t.rng.choice(['test', 'a.txt', 'a.TXT', 'a.fx', 'a.b.txt', 'x/y', 'a\\b',
                         'x//' + 'a'*43, 'x/' + 'b'*42, 'x/' + 'c'*100])
    ext = t.rng.choice([None, '', 'txt', 'TXT', 'fx'])
    t.w32(0x825D06A0, t.rng.choice([0, text(t,'1','option')]))
    t.args(r3=t.alloc(16,'assets'),r4=out,r5=t.rng.choice([-1,0,1,2,16,64,256]),
           r6=text(t,name,'name'),r7=text(t,ext,'extension') if ext is not None else 0)


def remove_input(t):
    value = t.rng.choice(['', 'abc', '..', '/..', '/..foo/', 'a/../b',
                           '/a/../b', 'a/b/c/../../d', 'a.b/c/../d',
                           'game:/a/../b', 'abc\\..\\def', 'ab/..\\foo'])
    t.args(r3=text(t,value,'pathAndGuards'))


def concat_input(t):
    prefix = t.rng.choice(['','abc','a'*32])
    out = t.alloc(256,'outputAndGuards')
    t.put(out,prefix.encode()+b'\0')
    source = text(t,t.rng.choice(['','test','x'*100]),'source')
    t.args(r3=out,r4=source,r5=t.rng.choice([-1,0,1,2,16,32,33,64,128]))


def build_input(t):
    assets = t.alloc(0x610,'assets')
    root = t.rng.randrange(4)
    depth = t.rng.randrange(5)
    t.w32(assets+0x600,depth)
    for i in range(8):
        t.put(assets+i*128, t.rng.choice(['','game:/','root/','a/b/../','//server/', 'x\\y\\']).encode()+b'\0')
    folder = t.rng.choice(['','folder/','a/b/../','/absolute/', 'game:/folder/','x\\y\\'])
    t.put(assets+(depth+3)*128, folder.encode()+b'\0')
    out=t.alloc(288,'pathOutputAndGuards')+16
    name=t.rng.choice(['test','a.txt','a.TXT','$/test','$/a.txt','/a/b','game:/test','a/b/../c'])
    ext=t.rng.choice([None,'','txt','fx'])
    t.args(r3=assets,r4=out,r5=t.rng.choice([-1,0,1,2,16,64,256]),
           r6=text(t,name,'name'),r7=text(t,ext,'extension') if ext is not None else 0,r8=root)
