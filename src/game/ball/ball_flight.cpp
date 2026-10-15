/**
 * ball_flight.cpp — the ball's flight and bounce model (see ball_flight.hpp)
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 */

#include "ball_flight.hpp"

#include <cmath>

// The VMX multiply-adds round the product; keep clang from fusing them.
#pragma clang fp contract(off)

struct pongBallInstance;

namespace {

using Vec4 = BallFlightVec4;

inline Vec4 Add(const Vec4& a, const Vec4& b) { return Vec4{a.x + b.x, a.y + b.y, a.z + b.z, a.w + b.w}; }
inline Vec4 Sub(const Vec4& a, const Vec4& b) { return Vec4{a.x - b.x, a.y - b.y, a.z - b.z, a.w - b.w}; }
inline Vec4 Mul(const Vec4& a, const Vec4& b) { return Vec4{a.x * b.x, a.y * b.y, a.z * b.z, a.w * b.w}; }
inline Vec4 Scale(const Vec4& a, float s) { return Vec4{a.x * s, a.y * s, a.z * s, a.w * s}; }
// vmsum3fp128: one rounding at the end (the float products are exact in double).
inline float Dot3(const Vec4& a, const Vec4& b) {
    return static_cast<float>(static_cast<double>(a.x) * b.x + static_cast<double>(a.y) * b.y +
                              static_cast<double>(a.z) * b.z);
}

// vpermwi128 99 and 135.
inline Vec4 YZX(const Vec4& a) { return Vec4{a.y, a.z, a.x, a.w}; }
inline Vec4 ZXY(const Vec4& a) { return Vec4{a.z, a.x, a.y, a.w}; }

// b × a the way both functions build it: a.zxy·b.yzx − a.yzx·b.zxy.
inline Vec4 CrossRev(const Vec4& a, const Vec4& b) { return Sub(Mul(ZXY(a), YZX(b)), Mul(YZX(a), ZXY(b))); }

struct ArchetypeView {             // rage::phArchetypePhys
    void** vtable;
    // Slot 12 (0x82162530) returns +0x24, the gravity factor slot 15 sets.
    float GetGravityFactor() { return reinterpret_cast<float (*)(void*)>(vtable[12])(this); }
};

struct BallInstView {              // pongBallInstance, a rage::phInst
    void**         vtable;
    ArchetypeView* archetype;      // +0x04
};

}  // namespace

extern pongBallInstance** g_ppBallInst;         // @ 0x8271A2F4  where the current ball instance is published
extern const BallFlightVec4 g_phGravity;        // @ 0x825CBCE0  (0, -9.8, 0, 0)
extern float g_ballSpinCoef;                    // @ 0x825C75F0  0.004
extern float g_ballDragCoef;                    // @ 0x825C8078  0.01
extern float g_ballDragCoefSwing10;             // @ 0x825C75FC  0.011, swing type 10 only
double crt_sqrt(double x);                      // @ 0x824301D0
double crt_tan(double x);                       // @ 0x82432628

// @ 0x822832D0
void BallFlight_Acceleration(BallFlightVec4* out, const BallFlightShotView* shot, const BallFlightVec4* vel,
                             const BallFlightVec4* spin) {
    *out = CrossRev(*vel, *spin);

    // (float)(pi / 3), as a double.
    float maxSideways = static_cast<float>(crt_tan(0x1.0c15236p+0));
    if (std::fabs(vel->x) >= std::fabs(vel->z) * maxSideways) {
        out->x = 0.0f;
        out->z = 0.0f;
    }

    float speedSq = Dot3(*vel, *vel);
    ArchetypeView* archetype = reinterpret_cast<BallInstView*>(*g_ppBallInst)->archetype;
    *out = Scale(*out, g_ballSpinCoef);

    if (speedSq > 1e-6f) {
        // The asm tests 8 and 9 first, both of which land on the default; the
        // recomp drops the third compare (== 10), so it reads as "8 and 9 differ".
        float drag = (shot->swingType == 10) ? g_ballDragCoefSwing10 : g_ballDragCoef;
        float speed = static_cast<float>(crt_sqrt(speedSq));
        *out = Sub(*out, Scale(*vel, speed * drag));
    }

    float gravityFactor = archetype->GetGravityFactor();
    *out = Add(Scale(g_phGravity, gravityFactor), *out);
}

// @ 0x822830E0
void BallFlight_Bounce(const BallFlightShotView* shot, const BallFlightVec4* normal, BallFlightVec4* pos,
                       BallFlightVec4* vel, BallFlightVec4* spin, float radius, float friction, float elasticity) {
    (void)shot;
    const Vec4 n = *normal;
    const Vec4 v = *vel;

    // Velocity of the contact point, one radius below the centre along -n.
    Vec4 contactVel = Add(Scale(CrossRev(n, *spin), -radius), v);
    float normalSpeed = Dot3(contactVel, n);
    float approach = -normalSpeed;

    Vec4 dv{0.0f, 0.0f, 0.0f, 0.0f};
    Vec4 dw{0.0f, 0.0f, 0.0f, 0.0f};
    if (approach > 0.0f) {
        float restitution = elasticity + 1.0f;
        float frictionLimit = approach * friction;
        Vec4 normalVel = Scale(n, normalSpeed);
        frictionLimit = frictionLimit * frictionLimit;
        Vec4 tangentVel = Sub(contactVel, normalVel);
        float tangentSq = Dot3(tangentVel, tangentVel);
        dv = Scale(normalVel, -restitution);

        if (tangentSq * 0.16f <= frictionLimit && frictionLimit > 1e-6f) {
            dv = Sub(dv, Scale(tangentVel, restitution * 0.4f));
        } else {
            float invTangent = (tangentSq == 0.0f) ? 0.0f : 1.0f / std::sqrt(tangentSq);
            dv = Add(Scale(tangentVel, invTangent * approach * friction * -2.0f), dv);
        }

        Vec4 lever = Scale(n, -(1.5f / radius));
        dw = CrossRev(dv, lever);
    }

    *vel = Add(v, dv);
    *spin = Add(*spin, dw);
    *pos = Add(Scale(*normal, 0.002f), *pos);
}
