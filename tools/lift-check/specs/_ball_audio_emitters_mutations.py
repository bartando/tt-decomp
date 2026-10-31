"""Each broken emitter lift must produce behavioral FAIL, not a build/spec error."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker,Options
CASES=[
 ('ball_audio_set_emitter_position',[
  ('empty update','    bool same=true;','    return;\n    bool same=true;'),
  ('wrong current position','fields->currentPosition+lane','fields->nextPosition+lane'),
  ('drop bit mask','next&g_affineXYZMask[lane]','next'),
  ('skip W compare','lane<4;','lane<3;'),
  ('invert unchanged gate','if (same) return;','if (!same) return;'),
  ('lose dirty flag','fields->flags|=0x80;','fields->flags|=0x40;'),
  ('overwrite published position','__builtin_memcpy(fields->nextPosition,position,16);','__builtin_memcpy(fields->currentPosition,position,16);'),
 ]),
 ('ball_audio_set_emitter_gain',[
  ('empty gain update','    if (__builtin_fabsf','    return;\n    if (__builtin_fabsf'),
  ('wrong change threshold','<0.005f','<0.01f'),
  ('remove lower clamp','if (gain<0.0f)','if (gain<-1.0f)'),
  ('wrong upper clamp','fields->gain=1.0f;','fields->gain=0.0f;'),
  ('clamp NaN','if (gain<0.0f)','if (!(gain>=0.0f))'),
  ('lose gain dirty flag','fields->flags|=1;','fields->flags|=2;'),
  ('skip negative warning','nop_8240E6D0("\\x1b[33maudControl::SetVolume < 0 attempted\\x1b[0m");','(void)gain;'),
 ]),
]
def main():
 root=Path(__file__).resolve().parents[3]
 source=(root/'src/game/ball/ball_audio_emitters.cpp').read_text()
 total=0
 for spec,mutations in CASES:
  for label,old,new in mutations:
   assert old in source,(spec,label)
   out=io.StringIO()
   with contextlib.redirect_stdout(out):
    rc=Checker(Path(__file__).with_name(spec+'.py'),Options(trials=128,seed=1,patches=((source,source.replace(old,new)),))).run()
   print(f"{'CAUGHT' if rc==1 else 'MISSED'} {spec}: {label}: {out.getvalue().splitlines()[0]}",flush=True)
   if rc!=1:
    print(out.getvalue());return 1
   total+=1
 print(f'Caught {total}/{total} mutations',flush=True)
 return 0
if __name__=='__main__':raise SystemExit(main())
