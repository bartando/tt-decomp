"""0x822EADF8: resource versions, late config reloads, lock release and handler install."""
from liftcheck.spec import *
FUNCTION='hudFlashBase_LoadPageGroup'
ADDRESS=0x822EADF8
SOURCE='src/rage/hud_page_load.cpp'
TRIALS=300
EXTERNS={'_snprintf':0x820C0B40,'g_fiAssetManager':0x825D0080,
 'g_sda_660D':0x8260660D,'g_swfCommandHandler':0x826066D4,
 'hudFlashBase_ScriptCommand':0x822EC418}
S={}


def push(c):
 p=0x825D0080+0x600
 depth=int.from_bytes(c.read(p,4),'big')
 c.write(p,((depth+1)&0xFFFFFFFF).to_bytes(4,'big'))
 c.write(S['config'],S['lateName'].to_bytes(4,'big'))


def path(c):
 assert c.in_stack(c.r(4))
 c.write(c.r(4),b'resolved\0'+bytes(119))


def snprintf(c):
 assert c.in_stack(c.r(3))
 c.write(c.r(3),b'$/resource/flash/movie\0')
 c.ret(r3=22)


def load(c):
 assert c.in_stack(c.r(3)) and c.in_stack(c.r(5)) and c.in_stack(c.r(6))
 c.write(c.r(5),S['imageBase'].to_bytes(4,'big'))
 c.write(c.r(6),S['size'].to_bytes(4,'big'))
 c.ret(r3=S['loadedFile'])


def resource(c):
 assert c.in_stack(c.r(3))
 c.write(c.r(3),S['scope'])


def allocate(c):
 c.write(S['hud']+0x40,S['newConfig'].to_bytes(4,'big'))
 c.write(S['hud']+0x58,S['lateFile'].to_bytes(4,'big'))
 c.ret(r3=S['allocation'])


def publish(c):c.write(S['hud']+0x5C,S['publishedMovie'].to_bytes(4,'big'))

CALLS={
 0x822E2E60:model(push,args=('r3','r4')),
 0x822E2B50:model(path,args=('r3','r5','r6','r7','r8')),
 0x820C0B40:model(snprintf,args=('r4','r5','r6','r7')),
 0x820F9380:model(load,args=('r4',)),
 0x82188190:model(resource,args=('r3','r4','r5','r6')),
 0x823F9EA0:stub(ret='void',args=('r3','r4'),deref={'r4':0x54}),
 0x82188220:stub(ret='void',args=('r3',),deref={'r3':0x54}),
 0x822EB2A8:stub(ret=lambda c:S['acquired'],args=('r3',)),
 0x820DEC88:model(allocate,args=('r3',)),
 0x823F8D08:stub(ret=lambda c:S['constructedMovie'],args=('r3','r4','r5','r6','r7','r8','r9')),
 0x822EB320:model(publish,args=('r3',)),
 0x8240E6D0:stub(ret='void',args=('r3','r4')),
}


def inputs(t):
 r=t.rng
 hud=t.alloc(0x70,'hud')
 configs=[]
 for i in range(2):
  config=t.alloc(0x20,f'config{i}')
  name=t.alloc(16,f'name{i}',fill=(b'movie' if i==0 else b'late')+b'\0')
  t.w32(config,name)
  t.w16(config+4,r.choice([0,1,9,128]))
  for off in [8,12,16,20,24]:t.w32(config+off,r.getrandbits(32))
  configs.append(config)
 t.w32(hud+0x40,configs[0])
 t.w32(hud+0x58,t.alloc(0x50,'existingFile') if t.index%4==0 else 0)
 t.w32(hud+0x5C,t.alloc(0xC0,'existingMovie') if t.index%3 else 0)
 t.w32(0x825D0080+0x600,r.getrandbits(32))
 t.w8(0x8260660D,r.randrange(256))
 t.w32(0x826066D4,r.getrandbits(32))
 S.update(hud=hud,config=configs[0],newConfig=configs[1],
  lateName=t.alloc(16,'changedName',fill=b'changed\0'),imageBase=r.getrandbits(32),size=r.getrandbits(32),
  loadedFile=t.alloc(0x60,'loadedFile') if t.index%5 else 0,lateFile=t.alloc(0x60,'lateFile'),
  allocation=t.alloc(0xAC,'allocation') if t.index%3 else 0,
  constructedMovie=t.alloc(0xAC,'constructedMovie'),publishedMovie=t.alloc(0xAC,'publishedMovie') if t.index%2 else 0,
  acquired=r.choice([0,1,128,256,257]),scope=r.randbytes(0x54))
 t.args(r3=hud,r4=r.getrandbits(32))
