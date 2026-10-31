#pragma once

#include "ball_flight.hpp"
#include <stdint.h>

namespace ballshot {
struct SolveSample {
    BallFlightVec4 velocity;
    uint8_t _pad10[0x20];
    float angle;                          // +0x30
    uint8_t _pad34[0x0C];
};
struct SolveSampleSet {
    SolveSample samples[32];
    float lowAngle, highAngle, step;       // +0x800
    int32_t count;                        // +0x80C
};
static_assert(sizeof(SolveSample) == 0x40, "trajectory sample layout");
static_assert(sizeof(SolveSampleSet) == 0x810, "trajectory sample-set layout");
}

int BallShot_Solve(void* entry, const BallFlightVec4* start, const BallFlightVec4* target,
                   BallFlightVec4* spin, BallFlightVec4* velocity, float speed); // @ 0x822851D0

// r6 is an unused argument slot. The final two integer arguments are passed
// on the caller's stack; the original solver reads their byte/pointer values.
int BallShot_SolveTrajectory(void* entry, const BallFlightVec4* start, const BallFlightVec4* target,
    int unusedR6, BallFlightVec4* spin, int firstFlag, BallFlightVec4* velocity, int secondFlag,
    bool stackFlag, ballshot::SolveSample* sample, float speed, float angle); // @ 0x822860D8
void BallShot_SampleAngles(void* entry, const BallFlightVec4* start, const BallFlightVec4* target,
    int unusedR6, BallFlightVec4* spin, ballshot::SolveSampleSet* samples, int increasing,
    float speed); // @ 0x82285A70
