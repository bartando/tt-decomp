#pragma once
struct bpVec4;

// Both originals always operate on the live prediction, irrespective of r4/r3.
void BallPredict_RetimeSamplesForLaunchVelocity(const bpVec4* velocity, int unusedBank); // @ 0x82289738
void BallPredict_ResetHitIds(int unusedBank); // @ 0x82289A08
