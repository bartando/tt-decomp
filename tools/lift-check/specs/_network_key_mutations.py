"""Key propagation, primary/fallback match and sentinel traversal checks."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
CASES={
 'network_key_target':[
  ('key equality','source->Query(key) == key','source->Query(key) != key'),
  ('query argument','source->Query(key)','source->Query(nullptr)'),
  ('source field','(sink, 0x24)','(sink, 0x20)'),
 ],
 'network_key_child':[
  ('primary field','(child, 0x18)','(child, 0x14)'),
  ('fallback field','(child, 0x1C)','(child, 0x18)'),
 ],
 'network_key_children':[
  ('early match','if (atSingleton_9B98_p39(child, key)) return 1;','if (atSingleton_9B98_p39(child, key)) return 0;'),
 ],
 'network_key_delegate':[
  ('forward key','msgMsgSink_3D70_p39(nested, key)','msgMsgSink_3D70_p39(nested, nullptr)'),
  ('delegate field','(this, 0x34)','(this, 0x30)'),
 ],
}
def main():
    source=(Path(__file__).resolve().parents[3]/'src/game/network/msg_sink_key.cpp').read_text()
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
