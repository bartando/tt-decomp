/**
 * ball_flight.hpp — the ball's flight and bounce model
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * The ball does not fly under RAGE's rigid-body solver during a rally. When a
 * shot is struck, the shot code (0x822827E8 and friends) simulates the whole
 * flight with the two functions below and the ball then plays the resulting
 * samples back (pg_70C8_g, called from gmBallNode::Update while a prediction
 * exists). The per-shot solver 0x82284078 and the trajectory sampler
 * 0x82288368 both step it the same way, at dt = 1 / round(game loop rate),
 * semi-implicit Euler (see BallFlight_Step).
 *
 * Shot entries are the 416-byte records of the per-player table at 0x8261A3D0;
 * the pongBallHitData ("shots.xml" fields) sits at +0x30, so Elasticity is at
 * +0xBC, Gravity at +0xC4 and SwingType at +0xCC.
 */
#pragma once

#include <stdint.h>

struct BallFlightVec4 {
    float x, y, z, w;
};

struct BallFlightShotView {        // one entry of the shot table at 0x8261A3D0
    uint8_t _pad000[0xBC];
    float   elasticity;            // +0xBC  hit data "Elasticity" (the table bounce's restitution)
    float   extraCornerBounceAngle;// +0xC0  "ExtraCornerBounceAngle"
    float   gravity;               // +0xC4  "Gravity"; 0x822827E8 turns it into the archetype's gravity factor
    uint8_t _pad0C8[0x04];
    int32_t swingType;             // +0xCC  "SwingType"; 10 gets the higher drag coefficient
};

// a = spinCoef · (ω × v)  − dragCoef · |v| · v  + g · gravityFactor, with the
// horizontal part of the spin term dropped once the ball travels more than 60°
// off the table's long axis (|v.x| ≥ |v.z| · tan 60°). g is the global gravity
// vector (0, -9.8, 0, 0) at 0x825CBCE0, gravityFactor the current ball
// archetype's (= shot Gravity / -9.8 while a shot is in the air).
void BallFlight_Acceleration(BallFlightVec4* out, const BallFlightShotView* shot, const BallFlightVec4* vel,
                             const BallFlightVec4* spin);

// Impulse bounce of a sphere of `radius` off a plane with unit `normal`. Only a
// ball whose contact point moves into the plane bounces. The normal part of the
// contact velocity is reflected with restitution `elasticity`; the tangential
// part either rolls (−0.4·(1+e)·v_t, 0.4 = 1/(1 + m r²/I) for a hollow ball)
// or, when 0.4·|v_t| exceeds friction·|v_n|, slides (−2·friction·|v_n| along
// v_t). The spin takes the matching angular impulse with I = 2/3·m·r². The ball
// is always pushed 2 mm out along the normal.
void BallFlight_Bounce(const BallFlightShotView* shot, const BallFlightVec4* normal, BallFlightVec4* pos,
                       BallFlightVec4* vel, BallFlightVec4* spin, float radius, float friction, float elasticity);

// One integration step as 0x82284078 inlines it: velocity first, then position
// with the new velocity (two non-fused VMX multiply-adds). The spin is constant
// in flight; only bounces change it.
inline void BallFlight_Step(BallFlightVec4* pos, BallFlightVec4* vel, const BallFlightVec4& accel, float dt) {
    BallFlightVec4 v{accel.x * dt, accel.y * dt, accel.z * dt, accel.w * dt};
    v = BallFlightVec4{v.x + vel->x, v.y + vel->y, v.z + vel->z, v.w + vel->w};
    BallFlightVec4 p{v.x * dt, v.y * dt, v.z * dt, v.w * dt};
    *pos = BallFlightVec4{p.x + pos->x, p.y + pos->y, p.z + pos->z, p.w + pos->w};
    *vel = v;
}
