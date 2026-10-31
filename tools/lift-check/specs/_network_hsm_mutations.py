"""Ancestor selection, state exit ordering and notification link guards."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
CASES={
 'network_hsm_common_parent':[
  ('parent field','load_ptr32<uint8_t>(state, 8)','load_ptr32<uint8_t>(state, 4)'),
  ('strict ancestor','if (contains(result, to)) return parent(to);','if (contains(result, to)) return to;'),
  ('same state','if (from == to) return result;','if (from == to) return from;'),
 ],
 'network_hsm_exit_to_parent':[
  ('transition limit','count == static_cast<uint32_t>(limit)','count != static_cast<uint32_t>(limit)'),
  ('cached child','parent(current);\n                *reinterpret_cast<rage::ptr32<void>*>(up + 0x0C) = current;','parent(current);\n                *reinterpret_cast<rage::ptr32<void>*>(up + 0x10) = current;'),
  ('pending count','++*reinterpret_cast<uint32_t*>(bytes + 0x54);','--*reinterpret_cast<uint32_t*>(bytes + 0x54);'),
  ('armed flag','bytes[0x68] &= 0x7F;','bytes[0x68] &= 0xBF;'),
 ],
 'network_hsm_enter_and_update':[
  ('entry child','load_ptr32<void>(active(), 0x0C);','load_ptr32<void>(active(), 0x10);'),
  ('status gate','status == 1 &&','status != 1 &&'),
  ('temporary limit','bytes + 0x58) = *reinterpret_cast<uint32_t*>(bytes + 0x54);','bytes + 0x58) = 0;'),
  ('restore limit','bytes + 0x58) = savedLimit;','bytes + 0x58) = savedLimit + 1;'),
 ],
 'network_hsm_notification_insert':[
  ('insert flag','!(link->flags & 0x80)','(link->flags & 0x80)'),
  ('successor backlink','if (next) next->previous = link;','if (next) next->previous = previous;'),
 ],
 'network_hsm_notification_remove':[
  ('remove flag','if (!link || (link->flags & 0x80))','if (!link || !(link->flags & 0x80))'),
  ('removed marker','link->flags |= 0x80;','link->flags |= 0x40;'),
 ],
}
def main():
    source=(Path(__file__).resolve().parents[3]/'src/rage/network/hsm_transition.cpp').read_text()
    total=0
    for spec,mutations in CASES.items():
        for label,old,new in mutations:
            assert source.count(old)==1,(spec,label,source.count(old))
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                rc=Checker(Path(__file__).with_name(spec+'.py'),Options(trials=192,seed=1,patches=((old,new),))).run()
            print(f"{spec}: {'CAUGHT' if rc==1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}",flush=True)
            if rc!=1:
                print(output.getvalue())
                return 1
            total+=1
    print(f'Caught {total}/{total} mutations',flush=True)
    return 0
if __name__=='__main__': raise SystemExit(main())
