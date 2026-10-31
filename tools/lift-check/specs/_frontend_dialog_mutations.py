"""Require behavioral failures for frontend selection and dialog completion."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
CASES=[
 ('frontend_input_highest_priority','src/game/frontend_input.cpp',[
  ('retain pending flag','queue[8] = 0;','queue[8] = 1;'),
  ('use blocklist','acceptsType = false;','acceptsType = true;'),
  ('drop subtype filter','subtype >= 0 &&','false &&'),
  ('unsigned priority','*reinterpret_cast<const int32_t*>(record + 4) >\n                     *reinterpret_cast<const int32_t*>(best + 4)','*reinterpret_cast<const uint32_t*>(record + 4) >\n                     *reinterpret_cast<const uint32_t*>(best + 4)'),
  ('last wins ties','*reinterpret_cast<const int32_t*>(record + 4) >','*reinterpret_cast<const int32_t*>(record + 4) >='),
  ('copy only header','sizeof(*output)','16'),
 ]),
 ('dialog_page_group_is_complete','src/game/frontend_page_group.cpp',[
  ('ignore completion value','if (done <= 0) return 0;','if (false) return 0;'),
  ('unsigned completion','if (done <= 0)','if (static_cast<uint32_t>(done) == 0)'),
  ('full acquire result','const uint8_t acquired = static_cast<uint8_t>(hudFlashBase_IsNetworkDirty(group));','const uint32_t acquired = hudFlashBase_IsNetworkDirty(group);'),
  ('wrong movie argument','swfGetPageGroupInteger(movie,','swfGetPageGroupInteger(group,'),
  ('do not close for pending input','static_cast<DialogClose*>(group)->Close();','/* close lost */'),
 ]),
 ('dialog_context_update','src/game/match/pong_states.cpp',[
  ('cache page across update','DialogPageGroup_IsComplete(rage::load_ptr32<void>(this, 0x18))','DialogPageGroup_IsComplete(group)'),
  ('wrong transition index','this) + 0x1C','this) + 0x18'),
  ('wrong transition root','hsmContext_SetNextState(g_loop_obj_ptr, next);','hsmContext_SetNextState(this, next);'),
 ])]

def main():
 root=Path(__file__).resolve().parents[3]
 total=0
 for spec,path,mutations in CASES:
  source=(root/path).read_text()
  for label,old,new in mutations:
   assert old in source,(spec,label)
   out=io.StringIO()
   with contextlib.redirect_stdout(out):
    rc=Checker(Path(__file__).with_name(spec+'.py'),Options(seed=1,patches=((old,new),))).run()
   print(f"{'CAUGHT' if rc==1 else 'MISSED'} {spec}: {label}: {out.getvalue().splitlines()[0]}",flush=True)
   if rc!=1:return 1
   total+=1
 print(f'Caught {total}/{total} mutations')
 return 0
if __name__=='__main__':raise SystemExit(main())
