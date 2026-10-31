"""Break every spatial-solver lift in checker cache copies; require behavioral FAIL.

The inverse's undefined C fourth-row padding is the only ignored output region.
Build errors, specification errors, and lift faults do not count as catches.
"""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker, Options
ROOT=Path(__file__).resolve().parents[3]
SOURCE='src/physics/ph_physics.cpp'
CASES={
 'ph_spatial_tensor_copy':('void phSpatialTensor_Copy(float* out, const float* input) {',[
  ('omit final vector','row < 12;','row < 11;'),
  ('wrong source vector','input + row * 4','input + ((row + 1) % 12) * 4'),
 ]),
 'ph_spatial_tensor_add':('void phSpatialTensor_Add(float* out, const float* input) {',[
  ('overwrite fourth-row padding','row < 3;','row < 4;'),
  ('subtract tensor','phFlushVmx(out[i]) + phFlushVmx(input[i])','phFlushVmx(out[i]) - phFlushVmx(input[i])'),
 ]),
 'ph_spatial_tensor_difference':('void phSpatialTensor_Difference(float* out, const float* input) {',[
  ('drop negation','out[i] = phFlushVmx(phFlushVmx(lbl_82606750[lane]) - phFlushVmx(out[i]));','out[i] = out[i];'),
  ('wrong staged block order','{0, 32, 16}','{0, 16, 32}'),
 ]),
 'ph_matrix_multiply3x3':('void phMatrix_Multiply3x3(float* out, const float* left, const float* right) {',[
  ('wrong source of W','old + row * 4','a + row * 4'),
  ('wrong right-hand column','b[4 + col]','b[4 + ((col + 1) % 3)]'),
 ]),
 'ph_matrix_invert_symmetric':('void phMatrix_InvertSymmetric(const float* m, float* out) {',[
  ('wrong cofactor sign','__builtin_fmaf(c, e, -bf)','__builtin_fmaf(c, e, bf)'),
  ('use upper triangle','b = m[4]','b = m[1]'),
 ]),
 'ph_matrix_invert_regularized':('void phMatrix_InvertRegularized(float* m, uint32_t stride) {',[
  ('omit pivot floor','const float minimum = trace * g_phInertiaPivotRatio;','const float minimum = 0.0f;'),
  ('wrong final off-diagonal sign','m[1] = m[stride] = -correction - firstTerm;','m[1] = m[stride] = correction - firstTerm;'),
 ]),
 'ph_matrix_rotate_diagonal':('void phMatrix_RotateDiagonal(const float* r, const float* d, float* out) {',[
  ('wrong diagonal mass','dz = d[2] * z','dz = d[0] * z'),
  ('wrong off-diagonal mirror','out[4] = out[1] = value;','out[4] = out[1] = -value;'),
 ]),
 'ph_articulated_body_build_inertia':('void phArticulatedBody_BuildInertia(void* object) {',[
  ('omit mass','const float mass = body[0x70 / 4];','const float mass = 1.0f;'),
  ('omit parallel-axis term','const float xmx = body[0xC0 / 4] * mx;','const float xmx = 0.0f;'),
 ]),
 'ph_spatial_tensor_invert':('void phSpatialTensor_Invert(const float* input, float* out) {',[
  ('omit cross-block negation','out[16 + i] = phFlushVmx(phFlushVmx(lbl_82606750[lane]) - phFlushVmx(out[16 + i]));','out[16 + i] = phFlushVmx(out[16 + i]);'),
  ('skip Schur inverse','phMatrix_InvertRegularized(out + 32, 4);','(void)out;'),
 ]),
 'ph_articulated_rebuild_solver':('void phArticulatedCollider_5D58(void* jointData) {',[
  ('skip inertia assembly','phArticulatedBody_BuildInertia(body);','(void)body;'),
  ('reduce wrong direction','for (int child = backwardCount - 1; child > 0; --child)','for (int child = 1; child < backwardCount; ++child)'),
  ('wrong backward virtual','joint->GetBackwardMatrix(jointMatrix);','joint->GetForwardMatrix(jointMatrix);'),
  ('skip final inversion','phSpatialTensor_Invert(reinterpret_cast<float*>(body + 0x250), reinterpret_cast<float*>(body + 0x310));','(void)body;'),
 ]),
 'ph_articulated_timestep_pipeline':('void rage::phArticulatedCollider::SetTimestep(float timestep) {',[
  ('omit root rebase','phArticulatedCollider_F0E0(this);','(void)this;'),
 ]),
}
def main():
 source=(ROOT/SOURCE).read_text(); total=0
 for spec,(signature,mutations) in CASES.items():
  start=source.index(signature); body=source[start:source.index('\n}\n',start)+2]
  for name,old,new in mutations:
   assert body.count(old)==1,(spec,name,body.count(old))
   output=io.StringIO()
   with contextlib.redirect_stdout(output):
    rc=Checker(Path(__file__).with_name(spec+'.py'),Options(trials=600,seed=1,patches=((body,body.replace(old,new)),))).run()
   report=output.getvalue(); caught=rc==1 and 'the lift faulted' not in report
   print(f"{spec}: {'CAUGHT' if caught else 'MISSED'} {name}: {report.splitlines()[0]}",flush=True)
   if not caught: print(report); return 1
   total+=1
 print(f'Caught {total}/{total} mutations',flush=True); return 0
if __name__=='__main__': raise SystemExit(main())
