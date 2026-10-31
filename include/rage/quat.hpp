#pragma once
namespace rage {
// Scalar product with the conjugate of right. W is stored first, followed by
// X/Y/Z; overlapping inputs observe each preceding store.
void quatMultiplyConjugate(float* out, const float* left, const float* right); // @ 0x8223B9A8
}

void* LocomotionStateAnim_BE20_g(void* out, void* left, void* right); // @ 0x8223BE20
