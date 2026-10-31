#include "crt/fp_helpers.hpp"

// CRT classification: +infinity, -infinity, quiet NaN, signaling NaN, other.
// The operation is entirely on the encoding, so it must not quiet an sNaN.
// @ 0x824357A8 | size: 0x84
int crt_fp_classify(double value) {
    uint64_t bits;
    __builtin_memcpy(&bits, &value, sizeof bits);
    if (bits == 0x7FF0000000000000ULL) return 1;
    if (bits == 0xFFF0000000000000ULL) return 2;
    const uint16_t tag = static_cast<uint16_t>(bits >> 48) & 0x7FF8u;
    if (tag == 0x7FF8u) return 3;
    if (tag == 0x7FF0u && (bits & 0x0007FFFFFFFFFFFFULL) != 0) return 4;
    return 0;
}

// This changes the encoded exponent without normalization or overflow checks.
// Even overflow into the sign bit is retained, as in the original halfword store.
// @ 0x82435770 | size: 0x34
double crt_fp_adjust_exponent(uint32_t /*unused*/, int delta, double value) {
    uint64_t bits;
    __builtin_memcpy(&bits, &value, sizeof bits);
    const uint32_t exponent = static_cast<uint32_t>((bits >> 52) & 0x7FFu);
    const uint16_t top = static_cast<uint16_t>(((exponent + static_cast<uint32_t>(delta)) << 4)
                         | ((bits >> 48) & 0x800Fu));
    bits = (bits & 0x0000FFFFFFFFFFFFULL) | (static_cast<uint64_t>(top) << 48);
    __builtin_memcpy(&value, &bits, sizeof value);
    return value;
}

// Addition/subtraction of 2^52 applies the current FP rounding mode. Preserve
// zeros (including -0) and values whose magnitude already makes them integral.
// @ 0x82436B30 | size: 0x44
double crt_fp_round(double value) {
    constexpr double integralLimit = 0x1p52;
    if (value == 0.0 || !(__builtin_fabs(value) < integralLimit)) return value;
    if (value < 0.0) {
        const double shifted = value - integralLimit;
        return shifted + integralLimit;
    }
    const double shifted = value + integralLimit;
    return shifted - integralLimit;
}

// @ 0x82436528 | size: 0x8
double crt_fp_sqrt(double value) {
    return __builtin_sqrt(value);
}
