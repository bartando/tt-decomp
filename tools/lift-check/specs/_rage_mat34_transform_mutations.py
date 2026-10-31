"""Behavioral mutation checks for the ball trail's affine point transform."""
import contextlib
import io
from pathlib import Path
from liftcheck.runner import Checker,Options
CASES=[
 ('empty transform','    float rows[16]','    return;\n    float rows[16]'),
 ('omit translation','row<4;','row<3;'),
 ('transpose basis','rows[row*4+axis]','rows[axis*4+row]'),
 ('ignore homogeneous mask','bits&g_affineXYZMask[lane]','bits'),
 ('omit homogeneous W','|g_affineHomogeneousW[lane]','|0u'),
 ('wrong leftover W','__builtin_memcpy(result+3,homogeneous,4);','result[3]=1.0f;'),
 ('overwrite matrix','__builtin_memcpy(point,result,16);','__builtin_memcpy(const_cast<float*>(matrix),result,16);'),
]
def main():
 root=Path(__file__).resolve().parents[3]
 src=(root/'src/rage/math/mat34_transform.cpp').read_text()
 for label,old,new in CASES:
  assert old in src,label
  out=io.StringIO()
  with contextlib.redirect_stdout(out):
   rc=Checker(Path(__file__).with_name('rage_mat34_transform_point_in_place.py'),Options(trials=96,seed=1,patches=((src,src.replace(old,new)),))).run()
  print(f"{'CAUGHT' if rc==1 else 'MISSED'} {label}: {out.getvalue().splitlines()[0]}",flush=True)
  if rc!=1:
   print(out.getvalue());return 1
 # Exercise the caller with the original transform, so its VMX basis math
 # cannot hide behind a randomly filled output boundary.
 src=(root/'src/game/ball/pong_ball.cpp').read_text()
 update_cases=[
  ('round dot products early',
   'return static_cast<float>((static_cast<double>(a.x) * b.x +\n        static_cast<double>(a.y) * b.y) + static_cast<double>(a.z) * b.z);',
   'return (a.x*b.x+a.y*b.y)+a.z*b.z;'),
  ('wrong reciprocal sqrt scale',
   'static_cast<float>(1.0 / __builtin_sqrt(static_cast<double>(lengthSq)))',
   'static_cast<float>(2.0 / __builtin_sqrt(static_cast<double>(lengthSq)))'),
 ]
 for label,old,new in update_cases:
  assert old in src,label
  out=io.StringIO()
  with contextlib.redirect_stdout(out):
   rc=Checker(Path(__file__).with_name('ball_update.py'),Options(trials=64,seed=1,patches=((src,src.replace(old,new)),))).run()
  print(f"{'CAUGHT' if rc==1 else 'MISSED'} {label}: {out.getvalue().splitlines()[0]}",flush=True)
  if rc!=1:
   print(out.getvalue());return 1
 total=len(CASES)+len(update_cases)
 print(f'Caught {total}/{total} mutations',flush=True)
 return 0
if __name__=='__main__':raise SystemExit(main())
