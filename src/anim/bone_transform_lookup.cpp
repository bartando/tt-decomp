// Compose a bone's authored offset with its sampled animation transform.
#include <cstdint>
#include "rage/mat33.hpp"
#include "rage/mat44.hpp"

extern "C" const float g_identityMatrixRef[16]; // @ 0x825CB800
extern void game_0A30(void*, void*, void*); // @ 0x821D0A30
extern void phMatrix_RotateZ(float*, double); // @ 0x82175D88
namespace rage {
extern void mat33RotateY(float*, double); // @ 0x82111EA0
}

namespace {
struct MatrixRow { float lane[4]; };
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
float flushVmx(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof bits);
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, sizeof value);
    }
    return value;
}
float translateLane(float basis, float amount, float position) {
    const float product = flushVmx(flushVmx(basis) * flushVmx(amount));
    return flushVmx(product + flushVmx(position));
}
}

// The sampling state is a pointer, and the output is four full 16-byte rows.
// Failed bone sampling retains the initialized reference transform.
// @ 0x821D0880 | size: 0x1AC
void phBoundCapsule_0880_g(void* bone, void* output, void* samplingState) {
    alignas(16) float sampled[16];
    __builtin_memcpy(sampled, g_identityMatrixRef, sizeof sampled);
    game_0A30(bone, sampled, samplingState);
    auto* matrix = static_cast<float*>(output);
    if (at<uint8_t>(bone, 0x42)) {
        // Preserve each basis row's w, just as the nine scalar stores do.
        matrix[0] = 1.0f; matrix[1] = 0.0f; matrix[2] = 0.0f;
        matrix[4] = 0.0f; matrix[5] = 1.0f; matrix[6] = 0.0f;
        matrix[8] = 0.0f; matrix[9] = 0.0f; matrix[10] = 1.0f;
        at<MatrixRow>(output, 0x30) = {};
        rage::mat33FromEuler(matrix, &at<float>(bone, 0x20));
        at<MatrixRow>(output, 0x30) = at<MatrixRow>(bone, 0x30);
        rage::mat44ComposeAffineInPlace(output, sampled);
        return;
    }
    __builtin_memcpy(output, sampled, sizeof sampled);
    rage::mat33RotateX(matrix, at<float>(bone, 0x20));
    rage::mat33RotateY(matrix, at<float>(bone, 0x24));
    phMatrix_RotateZ(matrix, at<float>(bone, 0x28));
    // Reload each authored component after the preceding translation store:
    // callers may overlap the bone record and the output matrix.
    for (unsigned axis = 0; axis < 3; ++axis) {
        const float amount = at<float>(bone, 0x30 + axis * 4);
        const MatrixRow basis = at<MatrixRow>(output, axis * 16);
        const MatrixRow position = at<MatrixRow>(output, 0x30);
        MatrixRow translated;
        for (unsigned lane = 0; lane < 4; ++lane)
            translated.lane[lane] = translateLane(basis.lane[lane], amount, position.lane[lane]);
        at<MatrixRow>(output, 0x30) = translated;
    }
}
