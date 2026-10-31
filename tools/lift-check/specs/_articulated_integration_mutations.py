"""Behavioral mutation proof for integration and its recovered matrix helpers."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT = Path(__file__).resolve().parents[3]
CASES = {
 'ph_articulated_integrate_positions': ('src/physics/ph_physics.cpp', 'void ph_IntegrateJointPositions(void* jointData, float timestep) {', [
  ('omit timestep', 'phFlushVmx(body[0x110 / 4 + lane]) * phFlushVmx(timestep)', 'phFlushVmx(body[0x110 / 4 + lane])'),
  ('skip angular integration', 'if (!(lengthSquared > g_phBoundSphere_DirEps))', 'if (true)'),
  ('wrong angular threshold', 'lengthSquared > g_phBoundSphere_DirEps', 'lengthSquared > 1.0f'),
  ('wrong multiplication order', 'mat33ComposeInPlace(transform, previous);', 'mat33ComposeInPlace(previous, transform);\n        memcpy(transform, previous, sizeof(transform));'),
  ('lose final basis row', 'memcpy(body + 0x90 / 4, transform, 48);', 'memcpy(body + 0x90 / 4, transform, 32);'),
 ]),
 'ph_articulated_build_rotation': ('src/physics/ph_physics.cpp', 'void phArticulatedCollider_BuildRotation(void*, float* out, const float* axis, double angle) {', [
  ('wrong sine sign', 'out[1] = xyScale - sinZ;', 'out[1] = xyScale + sinZ;'),
  ('drop cosine diagonal', '__builtin_fmaf(xx, scale, cosine)', '__builtin_fmaf(xx, scale, 0.0f)'),
  ('overwrite W padding', 'out[12] = out[13] = out[14] = g_phZeroFloat;', 'out[12] = out[13] = out[14] = out[15] = g_phZeroFloat;'),
 ]),
 'mat33_compose_in_place': ('src/rage/math/mat33.cpp', 'void mat33ComposeInPlace(float* matrix, const float* rotation) {', [
  ('include W in dot', 'k < 3;', 'k < 4;'),
  ('wrong right-hand column', 'right[k * 4 + col]', 'right[col * 4 + k]'),
  ('clear shuffled W', '__builtin_memcpy(result + row * 4 + 3, left + row * 4, 4);', 'result[row * 4 + 3] = 0.0f;'),
 ]),
}
def main():
 total=0
 for spec,(path,signature,mutations) in CASES.items():
  source=(ROOT/path).read_text(); start=source.index(signature); body=source[start:source.index('\n}\n',start)+2]
  for name,old,new in mutations:
   assert body.count(old)==1,(spec,name)
   output=io.StringIO()
   with contextlib.redirect_stdout(output):
    rc=Checker(Path(__file__).with_name(spec+'.py'),Options(trials=800,seed=1,patches=((body,body.replace(old,new)),))).run()
   report=output.getvalue(); caught=rc==1 and 'the lift faulted' not in report
   print(f"{spec}: {'CAUGHT' if caught else 'MISSED'} {name}: {report.splitlines()[0]}",flush=True)
   if not caught: print(report); return 1
   total+=1
 print(f'Caught {total}/{total} mutations',flush=True); return 0
if __name__=='__main__': raise SystemExit(main())
