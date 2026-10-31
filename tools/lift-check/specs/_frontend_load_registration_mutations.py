"""Resource-version ABI, callback reloads, and Flash loading side effects."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
CASES=[
 ('hud_flash_load_page_group','src/rage/hud_page_load.cpp',[
  ('wrong existing-file gate','if (!hud->file)','if (!hud->movie)'),
  ('drop load flags','g_sda_660D = config->loadFlags;','g_sda_660D = 0;'),
  ('drop asset pop','--*depth;','/* pop lost */'),
  ('wrong allocation size','rage_Alloc(0xAC)','rage_Alloc(0xA8)'),
  ('do not reload config','config = hud->config.get();\n            movie =','config = config;\n            movie ='),
  ('truncate final flags','config->flags);','static_cast<uint16_t>(config->flags));'),
  ('full lock result','const uint8_t acquired = static_cast<uint8_t>(hudFlashBase_IsNetworkDirty(hud));','const uint32_t acquired = hudFlashBase_IsNetworkDirty(hud);'),
  ('drop handler install','g_swfCommandHandler = hudFlashBase_ScriptCommand;','g_swfCommandHandler = nullptr;'),
 ]),
 ('credits_context_register','src/game/match/pong_states.cpp',[
  ('wrong version bias','g_creditsResourceVersion + 50u','g_creditsResourceVersion + 49u'),
  ('load context instead of group','hudFlashBase_LoadPageGroup(group, g_creditsResourceVersion','hudFlashBase_LoadPageGroup(this, g_creditsResourceVersion'),
 ]),
 ('dialog_context_register','src/game/match/pong_states.cpp',[
  ('publish stale group','g_dialogPageGroup = context->group.get();','g_dialogPageGroup = group;'),
  ('wrong version bias','g_dialogResourceVersion + 50u','g_dialogResourceVersion + 49u'),
 ]),
 ('legals_page_group_register','src/game/frontend_page_group.cpp',[
  ('wrong cached offset','group) + 0xEC','group) + 0xE8'),
  ('drop lock release','if (acquired != 0) hudFlashBase_PublishPageGroup(group);','/* release lost */'),
 ])]

def main():
 root=Path(__file__).resolve().parents[3]
 total=0
 signatures={
  'hud_flash_load_page_group':'extern "C" void hudFlashBase_LoadPageGroup(',
  'credits_context_register':'void pongCreditsContext::RegisterWithCreditsRoll(',
  'dialog_context_register':'void pongDialogContext::Register(',
  'legals_page_group_register':'void LegalsPageGroup_Register(',
 }
 for spec,path,cases in CASES:
  source=(root/path).read_text()
  start=source.index(signatures[spec])
  source=source[start:source.index('\n}',start)+2]
  for label,old,new in cases:
   assert source.count(old)==1,(spec,label,source.count(old))
   out=io.StringIO()
   with contextlib.redirect_stdout(out):
    rc=Checker(Path(__file__).with_name(spec+'.py'),Options(seed=1,patches=((source,source.replace(old,new)),))).run()
   print(f"{'CAUGHT' if rc==1 else 'MISSED'} {spec}: {label}: {out.getvalue().splitlines()[0]}",flush=True)
   if rc!=1:return 1
   total+=1
 print(f'Caught {total}/{total} mutations')
 return 0
if __name__=='__main__':raise SystemExit(main())
