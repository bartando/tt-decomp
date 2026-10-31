#include "rage/mat33.hpp"
#include "rage/math.hpp"
#include <cstring>

extern "C" const float lbl_8202D110; // @ 0x8202D110

namespace {
float angleOrZero(float y, float x, float zero) {
    if (x == zero && y == zero) return zero;
    return static_cast<float>(crt_atan2(y, x));
}
}

namespace rage {

// @ 0x82137B08
void mat33ToEuler(const float* matrix, float* angles) {
    alignas(16) float basis[16];
    std::memcpy(basis, matrix, 64);
    mat33Orthonormalize(basis);
    const float zero = lbl_8202D110;
    const float z = angleOrZero(basis[1], basis[0], zero);
    const float y = static_cast<float>(crt_asin(-basis[2]));
    const float x = angleOrZero(basis[6], basis[10], zero);
    angles[0] = x;
    angles[1] = y;
    angles[2] = z;
}

// @ 0x820D0658
void mat33ToEulerZXY(const float* matrix, float* angles) {
    alignas(16) float basis[16];
    std::memcpy(basis, matrix, 64);
    mat33Orthonormalize(basis);
    const float zero = lbl_8202D110;
    const float z = angleOrZero(basis[1], basis[5], zero);
    const float y = angleOrZero(basis[8], basis[10], zero);
    const float x = static_cast<float>(crt_asin(-basis[9]));
    // Retain the original store order for aliased output.
    angles[1] = y;
    angles[2] = z;
    angles[0] = x;
}

// @ 0x82234360
void mat33ToEulerXZY(const float* matrix, float* angles) {
    alignas(16) float basis[16];
    std::memcpy(basis, matrix, 64);
    mat33Orthonormalize(basis);
    const float z = static_cast<float>(crt_asin(-basis[4]));
    const float zero = lbl_8202D110;
    const float y = angleOrZero(basis[8], basis[0], zero);
    const float x = angleOrZero(basis[6], basis[5], zero);
    angles[0] = x;
    angles[1] = y;
    angles[2] = z;
}

} // namespace rage
