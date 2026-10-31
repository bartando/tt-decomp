#include "rage/math.hpp"
#include <cstdint>
#include <cstring>

// @ 0x82431D78 | size: 0x184
// Reduce the binary significands directly, preserving signed zero and gradual
// underflow. The retail CRT returns its negative quiet NaN for invalid inputs.
double crt_fmod(double value, double divisor) {
    uint64_t x, y;
    std::memcpy(&x, &value, sizeof(x));
    std::memcpy(&y, &divisor, sizeof(y));
    const uint64_t sign = x & UINT64_C(0x8000000000000000);
    x &= UINT64_C(0x7FFFFFFFFFFFFFFF);
    y &= UINT64_C(0x7FFFFFFFFFFFFFFF);
    const uint64_t infinity = UINT64_C(0x7FF0000000000000);
    uint64_t result;
    if (x >= infinity || y > infinity || y == 0) {
        result = UINT64_C(0xFFF8000000000000); // image constant @ 0x825B12B0
    } else if (x < y) {
        return value;
    } else if (x == y) {
        result = sign;
    } else {
        int ex = static_cast<int>(x >> 52);
        int ey = static_cast<int>(y >> 52);
        const uint64_t hiddenBit = UINT64_C(1) << 52;
        if (ex == 0) {
            ex = 1;
            while (x < hiddenBit) { x <<= 1; --ex; }
        } else {
            x = (x & (hiddenBit - 1)) | hiddenBit;
        }
        if (ey == 0) {
            ey = 1;
            while (y < hiddenBit) { y <<= 1; --ey; }
        } else {
            y = (y & (hiddenBit - 1)) | hiddenBit;
        }
        while (ex > ey) {
            if (x >= y) x -= y;
            if (x == 0) break;
            x <<= 1;
            --ex;
        }
        if (x >= y) x -= y;
        if (x != 0) {
            while (x < hiddenBit) { x <<= 1; --ex; }
            if (ex > 0) {
                x = (x - hiddenBit) | (static_cast<uint64_t>(ex) << 52);
            } else {
                x >>= 1 - ex;
            }
        }
        result = sign | x;
    }
    double out;
    std::memcpy(&out, &result, sizeof(out));
    return out;
}
