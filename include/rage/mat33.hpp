#pragma once

namespace rage {

// Write the xyz entries of three 16-byte rows, preserving padding. Axis is an
// aligned vec4 and need not be normalized; it may be null when angle is zero.
// Output and axis must be disjoint. The original accepts a double angle in f1.
void mat33RotationAxisAngle(float* out, const float* axis, double angle);

// XYZ Euler angles in radians; input may overlap output. Preserve row padding.
void mat33FromEuler(float* out, const float* angles); // @ 0x82118278

} // namespace rage
