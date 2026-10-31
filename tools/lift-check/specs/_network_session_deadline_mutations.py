"""Notifier links, timeout arming and message-sink deadline/cache callers."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
SESSION='src/rage/network/session_state_helpers.cpp'
SINK='src/game/network/msg_sink_timing.cpp'
IMAGE='src/graphics/image_descriptor_queries.cpp'
CHILDREN='src/game/network/msg_sink_children.cpp'
CASES={
 'network_sink_cleanup_children':(CHILDREN,[
  ('closing flag','->Delete(1);','->Delete(0);'),
  ('pending cleanup','    auto* head = bytes + 0x24;','    if (*reinterpret_cast<int32_t*>(bytes + 0x50) == 6) return;\n    auto* head = bytes + 0x24;'),
 ]),
 'network_sink_target_pending':(CHILDREN,[
  ('target offset','(sink, 0x24);\n    return target ? target->HasPending()','(sink, 0x20);\n    return target ? target->HasPending()'),
  ('raw result','target->HasPending() : 0','(target->HasPending() != 0) : 0'),
 ]),
 'network_sink_target_pause':(CHILDREN,[
  ('forward pause','target->SetPaused(paused)','target->SetPaused(0)'),
 ]),
 'network_sink_child_pending':(CHILDREN,[
  ('inner sink offset','(child, 0x18);\n    return sink ? msgMsgSink_8E60_sp(sink)','(child, 0x14);\n    return sink ? msgMsgSink_8E60_sp(sink)'),
 ]),
 'network_sink_child_pause':(CHILDREN,[
  ('child pause value','msgMsgSink_8E88_sp(sink, paused)','msgMsgSink_8E88_sp(sink, 1)'),
 ]),
 'network_sink_children_pending':(CHILDREN,[
  ('empty list','    return 0;','    return 1;'),
  ('boolean result','if (msgChild_HasPendingTarget(child)) return 1;','if (msgChild_HasPendingTarget(child)) return 2;'),
 ]),
 'network_sink_completed_session':(SINK,[
  ('status byte','static_cast<uint8_t>(target->GetState()) == 0xFF','target->GetState() == 0xFF'),
  ('completed status','== 0xFF;','== 0xFE;'),
 ]),
 'network_sink_adjusted_overrun':(SINK,[
  ('time adjustment','overrun + *reinterpret_cast<uint32_t*>(context + 0x28)','overrun - *reinterpret_cast<uint32_t*>(context + 0x28)'),
 ]),
 'network_sink_peer_ready':(SINK,[
  ('connection gate','word(0x158) != 8 && word(0x3C) != 1','word(0x158) != 8 || word(0x3C) != 1'),
  ('deadline comparison','word(0x178) > overrun','word(0x178) < overrun'),
  ('primary state','state != 5 && state != 6','state != 5 || state != 6'),
  ('peer kind mask','& 0xE0;','& 0xC0;'),
  ('secondary state','secondary + 0x50) != 3','secondary + 0x50) != 4'),
  ('tertiary state','tertiary + 0x50) != 3','tertiary + 0x50) != 4'),
 ]),
 'network_image_base_size':(IMAGE,[
  ('packed flag','return (words[1] & 1u)','return (words[1] & 2u)'),
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
  ('duration offset','int32_t msgSink_GetDeadlineOverrun(void* sink) {\n    auto* bytes = static_cast<uint8_t*>(sink);\n    if (*reinterpret_cast<uint32_t*>(bytes + 0x16C)','int32_t msgSink_GetDeadlineOverrun(void* sink) {\n    auto* bytes = static_cast<uint8_t*>(sink);\n    if (*reinterpret_cast<uint32_t*>(bytes + 0x168)'),
  ('deadline sign','bytes + 0x170) - paused -','bytes + 0x170) + paused -'),
 ]),
 'network_sink_dispatch_clock':(SINK,[
  ('forward flags','target->Dispatch(flags);','target->Dispatch(0);'),
  ('delegate offset','(owner, 0x24);\n    if (target) target->Dispatch(flags);','(owner, 0x20);\n    if (target) target->Dispatch(flags);'),
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
if __name__=='__main__':
 raise SystemExit(main())
