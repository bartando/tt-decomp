"""Notifier links, timeout arming and message-sink deadline/cache callers."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
SESSION='src/rage/network/session_state_helpers.cpp'
SINK='src/game/network/msg_sink_timing.cpp'
IMAGE='src/graphics/image_descriptor_queries.cpp'
CASES={
 'network_image_base_size':(IMAGE,[
  ('packed flag','words[1] & 1u','words[1] & 2u'),
  ('size mask','0x1FFFF800u','0x1FFFF000u'),
 ]),
 'network_image_aligned_size':(IMAGE,[
  ('ceiling adjustment','(words[4] >> 3) - 1u','(words[4] >> 3) + 1u'),
  ('fallback field','size == 0 ? words[3]','size == 0 ? words[2]'),
 ]),
 'network_session_register_notifier':(SESSION,[
  ('owner offset','reinterpret_cast<uint8_t*>(owner) + 8','reinterpret_cast<uint8_t*>(owner)'),
  ('count','++chain->count;','--chain->count;'),
  ('successor link','if (next) next->previous = node;','if (next) next->previous = previous;'),
 ]),
 'network_session_set_timeout':(SESSION,[
  ('armed bit','context[0x68] |= 0x80;','context[0x68] |= 0x40;'),
  ('deadline offset','context + 0x4C) =','context + 0x48) ='),
  ('deadline sign',' + static_cast<uint32_t>(milliseconds);',' - static_cast<uint32_t>(milliseconds);'),
 ]),
 'network_sink_deadline_overrun':(SINK,[
  ('pause sign','pausedAt > 0','pausedAt >= 0'),
  ('duration offset','bytes + 0x16C','bytes + 0x168'),
  ('deadline sign','bytes + 0x170) - paused -','bytes + 0x170) + paused -'),
 ]),
 'network_sink_dispatch_clock':(SINK,[
  ('forward flags','target->Dispatch(flags);','target->Dispatch(0);'),
  ('delegate offset','(owner, 0x24)','(owner, 0x20)'),
 ]),
 'network_sink_remove_peer':(SINK,[
  ('peer mask','(raw >> 5) & 7','(raw >> 4) & 7'),
  ('slot order','} else if (slot(0x18C) == key)', '} else if (slot(0x188) == key)'),
 ]),
 'network_sink_latch_peer_time':(SINK,[
  ('dispatch peer','peer->DispatchVirtualMethod(0);','DispatchVirtualMethod(0);'),
 ]),
 'network_sink_reset_peer_time':(SINK,[
  ('reset flag','*reinterpret_cast<uint32_t*>(bytes + 0x184) = 0;','*reinterpret_cast<uint32_t*>(bytes + 0x184) = 1;'),
 ]),
}
def main():
 root=Path(__file__).resolve().parents[3]
 total=0
 for spec,(path,mutations) in CASES.items():
  source=(root/path).read_text()
  for label,old,new in mutations:
   assert old in source,(spec,label)
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
if __name__=='__main__':
 raise SystemExit(main())
