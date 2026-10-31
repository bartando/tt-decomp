#include "rage/math.hpp"
#include <cstdint>
#include <cstring>

extern "C" double g_crtExpOverflow; // @ 0x825B12A8

namespace {
// fctid/fcfid: round through an integer, retaining the caller's rounding mode.
// All in-range double values at or above 2^52 are already integral. Saturated
// endpoints round back to the same doubles as the original conversion pair.
double roundExpExponent(double scaled) {
    if (!(scaled >= -0x1p63)) return -0x1p63;
    if (scaled >= 0x1p63) return 0x1p63;
    if (scaled >= 0x1p52 || scaled <= -0x1p52) return scaled;
    const double bias = scaled < 0.0 ? -0x1p52 : 0x1p52;
    const double shifted = scaled + bias;
    return shifted - bias;
}
int32_t expExponentWord(double integral) {
    if (!(integral > -2147483648.0)) return INT32_MIN;
    if (integral >= 2147483647.0) return INT32_MAX;
    return static_cast<int32_t>(integral);
}
}

// @ 0x82432478
// Coefficients are the exact read-only doubles at 0x82001798..0x820017FF.
// The original clamps subnormal results to zero and reconstructs the exponent
// by replacing its high halfword; use its arithmetic rather than host exp().
double crt_exp(double value) {
    const double exponent = roundExpExponent(value * 0x1.71547652b8ecbp+0);
    const double reduced = -__builtin_fma(exponent, 0x1.62e42fefa39efp-1, -value);
    const double square = reduced * reduced;
    double numerator = __builtin_fma(square, 0x1.152a46f58dc1cp-16, 0x1.c70e46fb3f6e0p-8);
    double denominator = __builtin_fma(square, 0x1.03f996fde3809p-11, 0x1.c718e714251b3p-5);
    numerator = __builtin_fma(numerator, square, 0.25);
    denominator = __builtin_fma(denominator, square, 0.5);
    numerator *= reduced;
    const double divisor = denominator - numerator;
    double result = numerator / divisor + 0.5;
    const uint32_t adjustment = static_cast<uint32_t>(expExponentWord(exponent)) + 1u;
    if (adjustment != 0) {
        uint64_t bits;
        std::memcpy(&bits, &result, 8);
        const uint32_t oldExponent = static_cast<uint32_t>((bits >> 52) & 0x7ffu);
        const uint16_t high = static_cast<uint16_t>(((oldExponent + adjustment) << 4)
                                                  | ((bits >> 48) & 0x800fu));
        bits = (bits & UINT64_C(0x0000ffffffffffff)) | (static_cast<uint64_t>(high) << 48);
        std::memcpy(&result, &bits, 8);
    }
    const double highDifference = value - 0x1.62e42fefa39f8p+9;
    if (highDifference >= 0.0) result = g_crtExpOverflow;
    const double lowDifference = -0x1.6232bdd7abcdap+9 - value;
    return lowDifference >= 0.0 ? 0.0 : result;
}
