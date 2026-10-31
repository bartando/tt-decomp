// Copy a bone's sampled matrix after converting its skeleton ID to an index.
#include <cstdint>
#include "locomotion.hpp"

extern void rage_debugLog(const char*, ...); // @ 0x8240E6D0
extern "C" const char g_boneMatrixLookupFailed[]; // @ 0x8203D34C

namespace {
template<class T> T& at(void* object, unsigned offset) {
    return *reinterpret_cast<T*>(static_cast<uint8_t*>(object) + offset);
}
struct MatrixRow { uint32_t lane[4]; };
}

// Both the output and the matrices in state are full 64-byte matrices.
// A failed lookup logs and leaves the destination untouched.
// @ 0x821D0A30 | size: 0xB0
void game_0A30(void* bone, void* output, void* state) {
    uint16_t index = 0;
    if (!LocomotionStateAnim_04F0_g(at<void*>(state, 4), at<uint16_t>(bone, 0x40), &index)) {
        rage_debugLog(g_boneMatrixLookupFailed);
        return;
    }
    auto* source = at<uint8_t*>(state, 0x14) + uint32_t(index) * 64;
    // Keep the original row load/store order, including overlapping matrices.
    at<MatrixRow>(output, 0) = at<MatrixRow>(source, 0);
    at<MatrixRow>(output, 0x10) = at<MatrixRow>(source, 0x10);
    at<MatrixRow>(output, 0x20) = at<MatrixRow>(source, 0x20);
    at<MatrixRow>(output, 0x30) = at<MatrixRow>(source, 0x30);
}
