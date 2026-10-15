/**
 * ph_math.cpp — the C runtime's sin, cos, atan2 and sqrt
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

// ph_physics.cpp's names. Its callers pass and keep floats.
float ph_Sinf(float x) { return static_cast<float>(crt_sin(x)); }
float ph_Cosf(float x) { return static_cast<float>(crt_cos(x)); }
float ph_Atan2f(float y, float x) { return static_cast<float>(crt_atan2(y, x)); }
float ph_Sqrtf(float x) { return static_cast<float>(crt_sqrt(x)); }
