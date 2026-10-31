#pragma once

namespace rage {

// Padded row-vector principal rotations. r3 = output, f1 = double angle;
// write xyz only, preserving row padding and any translation row.
void mat33RotationX(float* out, double angle); // @ 0x820C3F10
void mat33RotationY(float* out, double angle); // @ 0x820C3F98
void mat33RotationZ(float* out, double angle); // @ 0x820C4020

// Write the xyz entries of three 16-byte rows, preserving padding. Axis is an
// aligned vec4 and need not be normalized; it may be null when angle is zero.
// Output and axis must be disjoint. The original accepts a double angle in f1.
void mat33RotationAxisAngle(float* out, const float* axis, double angle);

// Rodrigues rotation with no normalization or axis validation. Write xyz only;
// overlapping output/axis storage observes the original's sequential reads.
void mat33RotationNormalizedAxis(float* out, const float* axis, double angle);

// Rotate rows 1 and 2 of an aligned matrix about local X, including both w lanes.
// Row 0 and any translation row remain untouched; VMX flushes denormals.
void mat33RotateX(float* matrix, double angle);

// XYZ Euler angles in radians; input may overlap output. Preserve row padding.
void mat33FromEuler(float* out, const float* angles); // @ 0x82118278

} // namespace rage
