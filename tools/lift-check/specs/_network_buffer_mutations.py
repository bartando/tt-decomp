"""Buffer initialization size, embedded link and backing-allocation ownership."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
CASES={
 'network_buffer_construct':[
  ('clear size','std::memset(bytes, 0, 0x8C);','std::memset(bytes, 0, 0x88);'),
  ('embedded link','bytes + 0x6C;','bytes + 0x68;'),
 ],
 'network_buffer_release':[
  ('backing field','(buffer, 0x78)','(buffer, 0x74)'),
  ('allocator tag','0xAB840003u','0xAB840001u'),
 ],
}
def main():
    source=(Path(__file__).resolve().parents[3]/'src/rage/audio/xact_buffer.cpp').read_text()
    total=0
    for spec,mutations in CASES.items():
        for label,old,new in mutations:
            assert source.count(old)==1,(spec,label,source.count(old))
            output=io.StringIO()
            with contextlib.redirect_stdout(output):
                rc=Checker(Path(__file__).with_name(spec+'.py'),Options(trials=128,seed=1,patches=((old,new),))).run()
            print(f"{spec}: {'CAUGHT' if rc==1 else 'MISSED'} {label}: {output.getvalue().splitlines()[0]}",flush=True)
            if rc!=1:
                print(output.getvalue())
                return 1
            total+=1
    print(f'Caught {total}/{total} mutations',flush=True)
    return 0
if __name__=='__main__': raise SystemExit(main())
