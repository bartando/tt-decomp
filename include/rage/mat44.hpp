#pragma once

namespace rage {
float mat44Determinant(const float* matrix); // @ 0x8223F008
// Compose an aligned affine transform in place. The original packs each input
// row's x into output w; translation is made homogeneous before source loads.
void mat44ComposeAffineInPlace(void* matrix, const void* transform); // @ 0x820C3AD8
// Transform an affine point in place; the final VMX merge retains input X in W.
void mat34TransformPointInPlace(const float* matrix,float* point); // @ 0x820D2038
}
