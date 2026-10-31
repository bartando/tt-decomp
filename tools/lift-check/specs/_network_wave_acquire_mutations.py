"""Wave bounds, acquisition ownership and property status/flag checks."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
CASES={
 'network_wave_record':[
  ('record stride','return records + slot * 0xFC;','return records + slot * 0xF8;'),
  ('record bound','if (slot >= count)','if (slot > count)'),
 ],
 'network_wave_descriptor':[
  ('descriptor bound','static_cast<uint16_t>(index) >= waveCount(bank, index)','static_cast<uint16_t>(index) > waveCount(bank, index)'),
  ('full index','return bank->GetDescriptor(index);','return bank->GetDescriptor(static_cast<uint16_t>(index));'),
 ],
 'network_wave_acquire':[
  ('dynamic flag','bank->GetDescriptor(index)[0] & 4','bank->GetDescriptor(index)[0] & 2'),
  ('wave ownership field','static_cast<uint8_t*>(cue) + 0x160','static_cast<uint8_t*>(cue) + 0x164'),
 ],
 'network_variable_set':[
  ('readonly gate','if (!(flags & 1) || (flags & 2))','if (!(flags & 1))'),
  ('forward setter flag','msgSlot_SetFloat(bytes, value, 0);','msgSlot_SetFloat(bytes, value, 1);'),
  ('changed value','else if (value != *reinterpret_cast<float*>(bytes + 0x14))','else if (value == *reinterpret_cast<float*>(bytes + 0x14))'),
 ],
 'network_variable_get':[
  ('reserved keys','index != 1 && index != 2','index != 1'),
  ('output field','*outValue = *reinterpret_cast<float*>(bytes + 0x14);','*outValue = *reinterpret_cast<float*>(bytes + 0x18);'),
 ],
}
def main():
    source=(Path(__file__).resolve().parents[3]/'src/rage/audio/xact_wave_acquire.cpp').read_text()
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
