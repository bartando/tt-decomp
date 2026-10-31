#pragma once
#include <cstdint>

namespace rage {
// VMX floating arithmetic flushes subnormal operands and results to signed
// zero. Scalar PPC arithmetic retains them, so reproduce that lane behavior.
inline float vmxFlushFloat(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof bits);
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, sizeof value);
    }
    return value;
}
inline float vmxAddFloat(float first, float second) {
    return vmxFlushFloat(vmxFlushFloat(first) + vmxFlushFloat(second));
}
}
