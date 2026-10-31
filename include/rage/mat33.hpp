#pragma once

namespace rage {

// Compose the xyz basis in place; translation stays untouched. VMX shuffles
// leave each input row's raw X bits in that output row's W lane.
void mat33ComposeInPlace(float* matrix, const float* rotation); // @ 0x820C3BC8

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
