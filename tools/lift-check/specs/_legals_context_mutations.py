"""The legals screen must use the Flash movie, exact keys, and callback reloads."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
CASES={
 'legals_context_input_poll':[
  ('skip fourth controller','controller < 4','controller < 3'),
  ('wrong button pointer','buttons + 48','buttons + 40'),
  ('wrong Flash target','swfGetOrCreatePageGroupValue(movie, g_legalsQuitKey)','swfGetOrCreatePageGroupValue(group, g_legalsQuitKey)'),
  ('wrong value tag','value->tag = 3','value->tag = 2'),
  ('forget input latch','bytes[0x18] = 1;','bytes[0x18] = 0;'),
  ('full lock result','const uint8_t acquired = static_cast<uint8_t>(hudFlashBase_IsNetworkDirty(group));','const uint32_t acquired = hudFlashBase_IsNetworkDirty(group);'),
 ],
 'legals_context_update':[
  ('wrong movie target','swfFindPageGroupValue(movie, g_legalsDoneKey)','swfFindPageGroupValue(group, g_legalsDoneKey)'),
  ('unsigned completion','if (done > 0)','if (static_cast<uint32_t>(done) > 0)'),
  ('wrong transition owner','hsmContext_SetNextState(g_loop_obj_ptr, 6)','hsmContext_SetNextState(this, 6)'),
  ('drop release','if (acquired != 0) hudFlashBase_PublishPageGroup(group);','/* release lost */'),
 ]}

def main():
 source=(Path(__file__).resolve().parents[3]/'src/game/match/pong_states.cpp').read_text()
 count=0
 for spec,mutations in CASES.items():
  signature='static void pongLegalsContext_InputPoll(' if spec.endswith('input_poll') else 'void pongLegalsContext::Update('
  start=source.index(signature)
  body=source[start:source.index('\n}',start)+2]
  for label,old,new in mutations:
   assert body.count(old)==1,(spec,label)
   out=io.StringIO()
   with contextlib.redirect_stdout(out):
    rc=Checker(Path(__file__).with_name(spec+'.py'),Options(seed=1,patches=((body,body.replace(old,new)),))).run()
   print(f"{'CAUGHT' if rc==1 else 'MISSED'} {spec}: {label}: {out.getvalue().splitlines()[0]}",flush=True)
   if rc!=1:return 1
   count+=1
 print(f'Caught {count}/{count} mutations')
 return 0
if __name__=='__main__':raise SystemExit(main())
