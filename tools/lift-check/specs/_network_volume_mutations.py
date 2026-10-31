"""Mute/solo gates, parent volume composition and child forwarding guards."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
CASES={
 'network_volume_group':[
  ('mute gate','if (muted[slot] != 0)','if (muted[slot] == 0)'),
  ('solo gate','(group + 0x74) != 0','(group + 0x74) == 0'),
  ('parent volume','volume = scale * volume;','volume = scale + volume;'),
 ],
 'network_volume_combined':[
  ('local volume','bytes + 0x58','bytes + 0x54'),
  ('fade composition','volume = volume * fade;','volume = volume + fade;'),
 ],
 'network_volume_target':[
  ('forward volume','target->SetVolume(volume);','target->SetVolume(0);'),
 ],
 'network_volume_child':[
  ('nested sink','if (!rage::load_ptr32<void>(child, 0x18)) return;','if (!rage::load_ptr32<void>(child, 0x1C)) return;'),
  ('child fade','scaled * fade);','scaled + fade);'),
 ],
 'network_volume_children':[
  ('list step','(child, 4);','(child, 8);'),
 ],
 'network_volume_set':[
  ('nonnegative clamp','volume >= zero ? volume : zero','volume < zero ? volume : zero'),
  ('propagate update','    msgMsgSink_3DC8_g(sink);','    (void)sink;'),
 ],
}
def main():
    source=(Path(__file__).resolve().parents[3]/'src/rage/audio/xact_volume.cpp').read_text()
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
