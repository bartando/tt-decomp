/**
 * ph_math.cpp — the C runtime's trigonometry and sqrt
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * The statically linked CRT's double-precision math (0x824301D0..0x8243110C;
 * the symbol map files them under phBoundCapsule). sin and cos reduce the
 * argument by multiples of pi in two parts and evaluate an odd polynomial;
 * atan2 folds the ratio into [0, 2 - sqrt 3] and evaluates a rational
 * approximation. The lifts repeat the original's operations, fused
 * multiply-adds included, so they give the same bits as the game.
 *
 * ph_physics.cpp calls them ph_Sinf, ph_Cosf, ph_Atan2f and ph_Sqrtf with
 * float arguments; those forward at the bottom.
 */

#include <cstdint>

// The mixed FP/integer Xenon interfaces leave GPR slots for FP arguments.
// Explicit unused slots keep these declarations callable under ppc32 SysV too.
uint32_t _ctrlfp(uint32_t desired, uint32_t mask);  // @ 0x82436530
int crt_fp_classify(double value);  // @ 0x824357A8
double crt_fp_adjust_exponent(uint32_t unused, int delta, double value);  // @ 0x82435770
double crt_fp_round(double value);  // @ 0x82436B30
double crt_fp_sqrt(double value);  // @ 0x82436528
double crt_fp_quiet_nan(int operation, uint32_t unused, uint32_t control, double value);  // @ 0x82436260
// flags in r3, operation in r4, saved control in r7; value/result in f1/f2.
double crt_fp_exception(uint32_t flags, int operation, uint32_t unused5, uint32_t unused6,
                        uint32_t control, double value, double result);  // @ 0x82436368

namespace {

struct crtSinCosConstants {       // @ 0x825B0A80
    double halfPi;                // +0x00
    double invPi;                 // +0x08
    double maxArg;                // +0x10  from here on the result is NaN
    float  zero;                  // +0x18
    float  one;                   // +0x1C
    float  minusOne;              // +0x20
    float  half;                  // +0x24
    double piHi;                  // +0x28  pi = piHi + piLo
    double piLo;                  // +0x30
    double poly[8];               // +0x38  r + r^3 * (poly[0] + z * (poly[1] + ...))
};

const crtSinCosConstants kSinCos = {
    0x1.921fb54442d18p+0,
    0x1.45f306dc9c883p-2,
    0x1.a39de00000000p+27,
    0.0f, 1.0f, -1.0f, 0.5f,
    0x1.921fb54400000p+1,
    0x1.0b4611a600000p-33,
    {-0x1.5555555555555p-3, 0x1.11111111110b0p-7, -0x1.a01a01a013e1ap-13, 0x1.71de3a524f063p-19,
     -0x1.ae6454b5dc0abp-26, 0x1.6123c686ad430p-33, -0x1.ae420dc08499cp-41, 0x1.880ff6993df95p-49},
};

const double kTrigNaN = -__builtin_nan("");   // @ 0x825B12B0, 0xFFF8000000000000

struct crtAtan2Constants {        // @ 0x825B0B60
    double tiny;                  // +0x00
    double halfPi;                // +0x08
    double pi;                    // +0x10
    double tan15;                 // +0x18  2 - sqrt 3
    double sqrt3Minus1;           // +0x20
    double sqrt3;                 // +0x28
    double huge;                  // +0x30
    double num[4];                // +0x38
    double den[4];                // +0x58
    double one;                   // +0x78
    double offset[4];             // +0x80  0, pi/6, pi/2, pi/3
    double minNormal;             // +0xA0
    float  zero;                  // +0xA8
    float  half;                  // +0xAC
    float  oneF;                  // +0xB0
};

const crtAtan2Constants kAtan2 = {
    0x1.6a09e667f3bcdp-27,
    0x1.921fb54442d18p+0,
    0x1.921fb54442d18p+1,
    0x1.126145e9ecd56p-2,
    0x1.76cf5d0b09955p-1,
    0x1.bb67ae8584caap+0,
    0x1.0000000000000p+1022,
    {-0x1.b60a651061ce2p+3, -0x1.4817fb9e2bccbp+4, -0x1.0fd3f5c8d6a63p+3, -0x1.acd7ad9b187bdp-1},
    {0x1.4887cbcc495a9p+5, 0x1.58a12040b6da5p+6, 0x1.dca0a320da3d7p+5, 0x1.e0c49e14ac710p+3},
    1.0,
    {0.0, 0x1.0c152382d7366p-1, 0x1.921fb54442d18p+0, 0x1.0c152382d7366p+0},
    0x1.0000000000000p-1022,
    0.0f, 0.5f, 1.0f,
};

struct crtAsinAcosConstants {      // @ 0x82001510
    double offset[4];             // 0, pi/4, pi/2, pi/4
    double tiny;
    double num[5];
    double den[5];
};

const crtAsinAcosConstants kAsinAcos = {
    {0.0, 0x1.921fb54442d18p-1, 0x1.921fb54442d18p+0, 0x1.921fb54442d18p-1},
    0x1.6a09e667f3bcdp-27,
    {-0x1.b5e55a83a0a62p+4, 0x1.c9aa7360ad48ap+5, -0x1.3d82ca9a6da9fp+5,
     0x1.44e1764ec3927p+3, -0x1.64bbdb5e61e65p-1},
    {-0x1.486c03e2b87ccp+7, 0x1.a124f101eb843p+8, -0x1.7ddcefc56a848p+8,
     0x1.2de7c96591c70p+7, -0x1.7d2e86ef9861fp+4},
};

// Fused multiply-add and square root as instructions (fmadd, fsqrt): the
// elementwise builtins never become libm calls, even in a freestanding build.
inline double Fma(double a, double b, double c) {
#if defined(__clang__)
    return __builtin_elementwise_fma(a, b, c);
#else
    return __builtin_fma(a, b, c);
#endif
}

inline double Sqrt(double x) {
#if defined(__clang__)
    return __builtin_elementwise_sqrt(x);
#else
    return __builtin_sqrt(x);
#endif
}

uint64_t Bits(double x) {
    uint64_t u;
    __builtin_memcpy(&u, &x, sizeof u);
    return u;
}

// fctidz: truncate to int64, saturating; NaN gives INT64_MIN.
int64_t ConvertTruncate(double v) {
    if (v != v || v <= -0x1p63) {
        return INT64_MIN;
    }
    if (v >= 0x1p63) {
        return INT64_MAX;
    }
    return static_cast<int64_t>(v);
}

// fctid in the default rounding mode: nearest, ties to even, saturating.
int64_t ConvertRound(double v) {
    if (v != v || v <= -0x1p63) {
        return INT64_MIN;
    }
    if (v >= 0x1p63) {
        return INT64_MAX;
    }
    int64_t i = static_cast<int64_t>(v);
    const double frac = v - static_cast<double>(i);
    if (frac > 0.5 || (frac == 0.5 && (i & 1) != 0)) {
        ++i;
    } else if (frac < -0.5 || (frac == -0.5 && (i & 1) != 0)) {
        --i;
    }
    return i;
}

double SinCosPoly(double r) {
    const double z = r * r;
    double p = Fma(kSinCos.poly[7], z, kSinCos.poly[6]);
    for (int k = 5; k >= 0; --k) {
        p = Fma(p, z, kSinCos.poly[k]);
    }
    p = Fma(p, z, 1.0);   // the 1.0 at 0x82079B08
    return p * r;
}

}  // namespace

// @ 0x824301D8 — sin (phBoundCapsule_01D8_g)
double crt_sin(double x) {
    const double ax = __builtin_fabs(x);
    const double sign = x >= 0.0 ? kSinCos.one : kSinCos.minusOne;
    const double n = static_cast<double>(ConvertRound(kSinCos.invPi * ax));
    const double r1 = -Fma(kSinCos.piHi, n, -ax);
    const bool odd = (ConvertTruncate(n) & 1) != 0;
    const double r = -Fma(kSinCos.piLo, n, -r1);
    double s = SinCosPoly(r);
    if (odd) {
        s = -s;
    }
    const double result = ax - kSinCos.maxArg >= 0.0 ? kTrigNaN : s * sign;
    return Bits(ax) == 0 ? x : result;
}

// @ 0x824302B0 — cos (phBoundCapsule_02B0_g): sin(|x| + pi/2), with the
// reduction centred so the polynomial stays the same.
double crt_cos(double x) {
    const double ax = __builtin_fabs(x);
    const double shifted = kSinCos.halfPi + ax;
    const double n = static_cast<double>(ConvertRound(kSinCos.invPi * shifted));
    const double m = n - kSinCos.half;
    const bool odd = (ConvertTruncate(n) & 1) != 0;
    const double r1 = -Fma(kSinCos.piHi, m, -ax);
    const double r = -Fma(kSinCos.piLo, m, -r1);
    double c = SinCosPoly(r);
    if (odd) {
        c = -c;
    }
    const double result = shifted - kSinCos.maxArg >= 0.0 ? kTrigNaN : c;
    return ax == kSinCos.zero ? static_cast<double>(kSinCos.one) : result;
}

// @ 0x82432628 — CRT tan, formerly misidentified as a tokenizer.
double crt_tan(double x) {
    constexpr uint32_t MASK = 0xC007FEFFu;
    const uint32_t control = _ctrlfp(0xF8, MASK);
    if ((Bits(x) & 0x7FF0000000000000ull) == 0x7FF0000000000000ull) {
        const int kind = crt_fp_classify(x);
        if (kind == 3) {
            return crt_fp_quiet_nan(32, 0, control, x);
        }
        return crt_fp_exception(8, 32, 0, 0, control, x,
                                kind > 0 && kind <= 2 ? kTrigNaN : x + 1.0);
    }
    if (x == 0.0) {
        _ctrlfp(control, MASK);
        return x;
    }
    if (__builtin_fabs(x) > 0x1.1c5831add62e4p+28) {
        return crt_fp_exception(40, 32, 0, 0, control, x, kTrigNaN);
    }
    const double n = crt_fp_round(x * 0x1.45f306dc9c883p-1);
    const double r1 = -Fma(0x1.921fb54400000p+0, n, -x);
    const double r = -Fma(0x1.0b4611a600000p-34, n, -r1);
    double numerator = r;
    double denominator = 1.0;
    if (__builtin_fabs(r) < 0x1.6a09e667f3bcdp-27) {
        if ((Bits(r) & 0x7FF0000000000000ull) == 0 && r != 0.0) {
            const double adjusted = crt_fp_adjust_exponent(0, 1536, r);
            return crt_fp_exception(18, 32, 0, 0, control, x, adjusted);
        }
    } else {
        const double z = r * r;
        double p = -Fma(z, 0x1.2bab72ea2c724p-16, -0x1.c0e82a63baadfp-9);
        double q = Fma(z, 0x1.0b774f07678e9p-21, -0x1.46f6499094841p-12);
        p = Fma(p, z, -0x1.112b5e54d0900p-3);
        q = Fma(q, z, 0x1.a479ea17e2159p-6);
        p = Fma(p, z, 1.0);
        q = Fma(q, z, -0x1.ddeb047fbd9d5p-2);
        numerator = p * r;
        denominator = Fma(q, z, 1.0);
    }
    const double result = (ConvertTruncate(__builtin_fabs(n)) & 1) != 0
        ? denominator / -numerator : numerator / denominator;
    if ((control & 8) == 0) {
        return crt_fp_exception(16, 32, 0, 0, control, x, result);
    }
    _ctrlfp(control, MASK);
    return result;
}

// @ 0x82430FE0 — atan2(y, x) (phBoundCapsule_0FE0_g)
double crt_atan2(double y, double x) {
    const bool yNegative = (Bits(y) >> 63) != 0;
    double angle;
    if (x == kAtan2.zero) {
        if (y == kAtan2.zero) {
            if ((Bits(x) >> 63) == 0) {
                return y;
            }
            return yNegative ? -kAtan2.pi : kAtan2.pi;
        }
        angle = kAtan2.halfPi;
    } else {
        double num = __builtin_fabs(y);
        double den = __builtin_fabs(x);
        int octant = 0;
        if (!(num <= den)) {   // a NaN swaps too
            const double t = num;
            num = den;
            den = t;
            octant = 2;
        }
        double t = num / den;
        if (!(t <= kAtan2.tan15)) {
            ++octant;
            const double denom = kAtan2.sqrt3 + t;
            t = Fma(kAtan2.sqrt3, t, -static_cast<double>(kAtan2.oneF)) / denom;
        }
        const double z = t * t;
        double q = kAtan2.den[3] + z;
        double p = Fma(kAtan2.num[3], z, kAtan2.num[2]);
        q = Fma(q, z, kAtan2.den[2]);
        p = Fma(p, z, kAtan2.num[1]);
        q = Fma(q, z, kAtan2.den[1]);
        p = Fma(p, z, kAtan2.num[0]);
        q = Fma(q, z, kAtan2.den[0]);
        double a = p * z * t / q + t;
        if (octant > 1) {
            a = -a;
        }
        angle = kAtan2.offset[octant] + a;
    }
    double result = x >= 0.0 ? angle : kAtan2.pi - angle;
    if (yNegative) {
        result = -result;
    }
    return result;
}

// @ 0x824301D0 — sqrt (phBoundCapsule_01D0_g): fsqrt
double crt_sqrt(double x) {
    return Sqrt(x);
}

// @ 0x82430BA8
// Shared CRT asin/acos core (formerly fiAsciiTokenizer_0BA8_g), size 0x2DC.
// f1 = x, r4 = selector (0 asin, 1 acos), return in f1. r3 is unused;
// retain its slot explicitly because SysV does not reserve it for x.
// The only entry thunks, 0x82430E88/0x82430E90, supply selectors 0/1.
double crt_asin_acos(double x, uint32_t /*unused*/, int acosMode) {
    constexpr uint32_t CONTROL_MASK = 0xC007FEFFu;
    const uint32_t control = _ctrlfp(0xF8, CONTROL_MASK);
    const int operation = acosMode != 0 ? 13 : 14;

    if ((Bits(x) & 0x7FF0000000000000ull) == 0x7FF0000000000000ull) {
        const int kind = crt_fp_classify(x);
        if (kind == 3) {
            return crt_fp_quiet_nan(operation, 0, control, x);
        }
        const double result = kind > 0 && kind <= 2 ? kTrigNaN : x + 1.0;
        return crt_fp_exception(8, operation, 0, 0, control, x, result);
    }

    double result;
    if (x == 0.0 && acosMode == 0) {
        result = x;  // preserve asin(-0)
    } else {
        double reduced = x < 0.0 ? -x : x;
        int region = acosMode;
        if (reduced < kAsinAcos.tiny) {
            result = reduced;
            if ((Bits(reduced) & 0x7FF0000000000000ull) == 0 && reduced != 0.0) {
                // The CRT exponent helper changes the field directly; this
                // is deliberately not ldexp (subnormals are not normalized).
                result = crt_fp_adjust_exponent(0, 1536, x);
                return crt_fp_exception(18, operation, 0, 0, control, x, result);
            }
        } else {
            double z;
            if (reduced > 0.5) {
                region = 1 - acosMode;
                if (reduced > 1.0) {
                    return crt_fp_exception(8, operation, 0, 0, control, x, kTrigNaN);
                }
                if (reduced == 1.0) {
                    if (acosMode != 0 && x >= 0.0) {
                        _ctrlfp(control, CONTROL_MASK);
                        return 0.0;
                    }
                    reduced = 0.0;
                    z = 0.0;
                } else {
                    z = crt_fp_adjust_exponent(0, -1, 1.0 - reduced);
                    reduced = crt_fp_adjust_exponent(0, 1, -crt_fp_sqrt(z));
                }
            } else {
                z = reduced * reduced;
            }

            // Keep the binary's individual fmadd/fmsub/fnmsub roundings.
            double p = -Fma(z, -kAsinAcos.num[4], -kAsinAcos.num[3]);
            double q = z + kAsinAcos.den[4];
            p = Fma(p, z, kAsinAcos.num[2]);
            q = Fma(q, z, kAsinAcos.den[3]);
            p = Fma(p, z, kAsinAcos.num[1]);
            q = Fma(q, z, kAsinAcos.den[2]);
            p = Fma(p, z, kAsinAcos.num[0]);
            q = Fma(q, z, kAsinAcos.den[1]);
            q = Fma(q, z, kAsinAcos.den[0]);
            result = ((p * z) * reduced) / q + reduced;
        }

        if (acosMode == 0) {
            if (region != 0) {
                const double offset = kAsinAcos.offset[region];
                result = (offset + result) + offset;
            }
            if (x < 0.0) {
                result = -result;
            }
        } else {
            const double offset = kAsinAcos.offset[x < 0.0 ? region + 2 : region];
            result = (x < 0.0 ? offset + result : offset - result) + offset;
        }

        if ((control & 8) == 0) {
            return crt_fp_exception(16, operation, 0, 0, control, x, result);
        }
    }

    _ctrlfp(control, CONTROL_MASK);
    return result;
}

// The core's two entry thunks: `li r4, 0|1` then a branch, r3 passed through.
// @ 0x82430E88
double crt_asin(double x) {
    return crt_asin_acos(x, 0, 0);
}

// @ 0x82430E90
double crt_acos(double x) {
    return crt_asin_acos(x, 0, 1);
}

// ph_physics.cpp's names. Its callers pass and keep floats.
float ph_Sinf(float x) { return static_cast<float>(crt_sin(x)); }
float ph_Cosf(float x) { return static_cast<float>(crt_cos(x)); }
float ph_Atan2f(float y, float x) { return static_cast<float>(crt_atan2(y, x)); }
float ph_Sqrtf(float x) { return static_cast<float>(crt_sqrt(x)); }

// @ 0x82431910
double crt_floor(double x) {
    const double truncated = static_cast<double>(ConvertTruncate(x));
    const double magnitude = __builtin_fabs(x);
    const double rounded = x - truncated >= 0.0 ? truncated : truncated - 1.0;
    const double result = 1.0e18 - magnitude >= 0.0 ? rounded : x;
    return -magnitude >= 0.0 ? x : result;
}
