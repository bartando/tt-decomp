"""Break spatial multiplication, tree response, and velocity force preparation."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT=Path(__file__).resolve().parents[3]
SOURCE='src/physics/ph_physics.cpp'
CASES={
 'ph_spatial_tensor_multiply': ('void phSpatialTensor_Multiply(const float* matrix, const float* input, float* output) {',[
  ('drop first transpose','if (stage == 0) {','if (stage == 9) {'),
  ('reuse first input vector','memcpy(value, input + inputVector, sizeof(value));','memcpy(value, input, sizeof(value));'),
  ('lose shuffled W','result[3] = result[0];','result[3] = 0.0f;'),
  ('subtract coupled block','phFlushVmx(target[lane]) + phFlushVmx(result[lane])','phFlushVmx(target[lane]) - phFlushVmx(result[lane])'),
 ]),
 'ph_articulated_prepare_force_response': ('void phArticulatedCollider_PrepareForceResponse(void* jointData) {',[
  ('retain half local forces','memset(body + 0x170 / 4, 0, 32);','memset(body + 0x170 / 4, 0, 16);'),
  ('reduce in wrong order','for (int child = backwardCount - 1; child > 0; --child)','for (int child = 1; child < backwardCount; ++child)'),
  ('wrong reduction virtual','joint->ResolveParentResponse(body + 0x3F0 / 4, reduced);','joint->ResolveChildResponse(body + 0x3F0 / 4, reduced);'),
  ('wrong propagated difference','phFlushVmx(parent[0x3F0 / 4 + lane]) - phFlushVmx(reduced[lane])','phFlushVmx(parent[0x3F0 / 4 + lane]) + phFlushVmx(reduced[lane])'),
  ('subtract child response','phFlushVmx(body[0x3F0 / 4 + lane]) + phFlushVmx(propagated[lane])','phFlushVmx(body[0x3F0 / 4 + lane]) - phFlushVmx(propagated[lane])'),
 ]),
 'ph_articulated_prepare_forces': ('void phArticulatedCollider_5FE0(void* jointData) {',[
  ('skip tree solve','phArticulatedCollider_PrepareForceResponse(jointData);','(void)jointData;'),
  ('subtract force response','phFlushVmx(body[0x130 / 4 + lane]) + phFlushVmx(body[0x3F0 / 4 + lane])','phFlushVmx(body[0x130 / 4 + lane]) - phFlushVmx(body[0x3F0 / 4 + lane])'),
  ('copy wrong angular velocity','memcpy(body + 0x120 / 4, body + 0x130 / 4, 16);','memcpy(body + 0x120 / 4, body + 0x140 / 4, 16);'),
  ('omit origin recovery','phRecoverOriginVelocity(body);','(void)body;'),
 ]),
}
def main():
 source=(ROOT/SOURCE).read_text(); total=0
 for spec,(signature,mutations) in CASES.items():
  start=source.index(signature); body=source[start:source.index('\n}\n',start)+2]
  for name,old,new in mutations:
   assert body.count(old)==1,(spec,name)
   out=io.StringIO()
   with contextlib.redirect_stdout(out): rc=Checker(Path(__file__).with_name(spec+'.py'),Options(trials=800,seed=1,patches=((body,body.replace(old,new)),))).run()
   report=out.getvalue(); caught=rc==1 and 'the lift faulted' not in report
   print(f"{spec}: {'CAUGHT' if caught else 'MISSED'} {name}: {report.splitlines()[0]}",flush=True)
   if not caught: print(report); return 1
   total+=1
 print(f'Caught {total}/{total} mutations',flush=True); return 0
if __name__=='__main__': raise SystemExit(main())
