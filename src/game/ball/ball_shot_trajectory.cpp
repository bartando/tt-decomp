// Angle sampling and iterative launch-trajectory search.
#include "ball_shot_solve.hpp"
#include <cmath>
#include <stdint.h>

extern int32_t g_shotSolveState;             // @ 0x82606580
extern "C" const float lbl_82619BF0[4];      // @ 0x82619BF0
extern "C" const float lbl_82606750[4];      // @ 0x82606750
extern "C" const float lbl_825CB7C0[4];      // @ 0x825CB7C0
extern "C" const float lbl_825CB7D0[4];      // @ 0x825CB7D0

namespace {
using Vec4 = BallFlightVec4;

float FlushVmx(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof(bits));
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, sizeof(bits));
    }
    return value;
}

float Dot3(const Vec4& a, const Vec4& b) {
    double sum = static_cast<double>(FlushVmx(a.x)) * FlushVmx(b.x);
    sum += static_cast<double>(FlushVmx(a.y)) * FlushVmx(b.y);
    sum += static_cast<double>(FlushVmx(a.z)) * FlushVmx(b.z);
    return FlushVmx(static_cast<float>(sum));
}

Vec4 RefinedInverseLength(float squareLength) {
    const float estimate = FlushVmx(static_cast<float>(1.0 / __builtin_sqrt(static_cast<double>(squareLength))));
    Vec4 result;
    float* output = &result.x;
    for (int lane = 0; lane < 4; ++lane) {
        const float y = estimate == FlushVmx(lbl_82619BF0[lane]) ? lbl_82606750[lane] : estimate;
        const float square = FlushVmx(FlushVmx(y) * FlushVmx(y));
        const float halfY = FlushVmx(FlushVmx(lbl_825CB7D0[lane]) * FlushVmx(y));
        const float error = FlushVmx(-FlushVmx(FlushVmx(squareLength * square)
                                                    - FlushVmx(lbl_825CB7C0[lane])));
        output[lane] = FlushVmx(FlushVmx(error * halfY) + FlushVmx(y));
    }
    return result;
}

Vec4 MulVmx(const Vec4& a, const Vec4& b) {
    return {FlushVmx(FlushVmx(a.x) * FlushVmx(b.x)),
            FlushVmx(FlushVmx(a.y) * FlushVmx(b.y)),
            FlushVmx(FlushVmx(a.z) * FlushVmx(b.z)),
            FlushVmx(FlushVmx(a.w) * FlushVmx(b.w))};
}
}

// @ 0x82285A70
void BallShot_SampleAngles(void* entry, const Vec4* start, const Vec4* target,
    int /*unusedR6*/, Vec4* spin, ballshot::SolveSampleSet* samples, int increasing,
    float speed) {
    int count = 0;
    if (static_cast<uint8_t>(increasing) != 0) {
        float angle = samples->lowAngle;
        if (angle < samples->highAngle) {
            do {
                if (count >= 32) break;
                auto* sample = &samples->samples[count];
                sample->angle = angle;
                g_shotSolveState = 0;
                BallShot_SolveTrajectory(entry, start, target, 0, spin, 0, &sample->velocity,
                                         0, false, sample, speed, angle);
                angle += samples->step;
                ++count;
            } while (angle < samples->highAngle);
        }
    } else {
        float angle = samples->highAngle;
        if (angle > samples->lowAngle) {
            do {
                if (count >= 32) break;
                auto* sample = &samples->samples[count];
                sample->angle = angle;
                g_shotSolveState = 0;
                BallShot_SolveTrajectory(entry, start, target, 0, spin, 0, &sample->velocity,
                                         0, false, sample, speed, angle);
                const float squareLength = Dot3(sample->velocity, sample->velocity);
                const Vec4 inverse = RefinedInverseLength(squareLength);
                const float length = FlushVmx(squareLength * FlushVmx(inverse.x));
                float limit;
                __builtin_memcpy(&limit, static_cast<const uint8_t*>(entry) + 0xB0, sizeof(limit));
                if (length > 0.0f) {
                    const Vec4 normalized = MulVmx(sample->velocity, inverse);
                    if (length > limit) {
                        sample->velocity = MulVmx(normalized, Vec4{limit, limit, limit, limit});
                    }
                }
                angle -= samples->step;
                ++count;
            } while (angle > samples->lowAngle);
        }
    }
    samples->count = count;
}

extern double crt_sqrt(double value);       // @ 0x824301D0
extern double crt_sin(double value);        // @ 0x824301D8
extern double crt_cos(double value);        // @ 0x824302B0
extern double crt_asin(double value);       // @ 0x82430E88
extern float ph_Atan2fSafe(float y, float x); // @ 0x820D0550
namespace rage {
void cosSin(float* cosine, float* sine, double angle); // @ 0x820D04F0
}
extern void nop_8240E6D0(const char* text, ...); // @ 0x8240E6D0
extern void* g_pTableDims;                     // @ 0x8271A304
extern void** g_ppBallInst;                    // @ 0x8271A2F4
extern "C" float g_fastOrbitMul;               // @ 0x825C8A50
extern "C" float g_ballDragCoef;               // @ 0x825C8078
extern "C" const float g_ambientCubeFalloff;   // @ 0x825C8084
extern "C" float g_ballTableSurfaceOffset;     // @ 0x826064B8

// The flight/contact simulator: all eight register arguments are used; the
// optional contact report is its ninth integer argument, on the caller stack.
extern void BallShot_SimulateTrajectory(void* entry, const Vec4* start,
    const Vec4* velocity, const Vec4* spin, const Vec4* target, int firstFlag,
    Vec4* result, int stackFlag, ballshot::TrajectoryContacts* contacts); // @ 0x82284078

namespace {
struct TrajectoryTable {
    uint8_t _pad00[0x10];
    float width, height, depth;
};
struct TrajectoryBound { uint8_t _pad00[8]; float radius; };
struct TrajectoryArchetype { uint8_t _pad00[0x0C]; TrajectoryBound* bound; };
struct TrajectoryBall { void* vtable; TrajectoryArchetype* archetype; };

float CurrentBallRadius() {
    auto* ball = static_cast<TrajectoryBall*>(*g_ppBallInst);
    return ball ? ball->archetype->bound->radius : 0.0f;
}

float EntryMaxAngle(void* entry) {
    float result;
    __builtin_memcpy(&result, static_cast<const uint8_t*>(entry) + 0x178, sizeof(result));
    return result;
}

float WrapAngle(float angle) {
    constexpr float pi = 3.1415927410125732f;
    constexpr float twoPi = 6.2831854820251465f;
    if (angle > pi) return angle - twoPi;
    if (angle < -pi) return angle + twoPi;
    return angle;
}

float ClampStep(float value, float lower, float upper) {
    const float aboveLower = value - lower;
    const float limited = aboveLower >= 0.0f ? value : lower;
    const double aboveUpper = static_cast<double>(limited) - upper;
    return aboveUpper >= 0.0 ? upper : limited;
}

bool NegativeSign(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof(bits));
    return (bits >> 31) != 0;
}

// Solve the two-dimensional finite-difference Jacobian. The singular fallback
// deliberately tests the second step without abs(), matching the original.
bool SolveCorrection(float yawX, float yawZ, float otherX, float otherZ,
                     float errorX, float errorZ, float& yawStep, float& otherStep) {
    const float product = otherX * yawZ;
    const float determinant = __builtin_fmaf(otherZ, yawX, -product);
    if (__builtin_fabsf(determinant) > 0.0000009999999974752427f) {
        const float xProduct = otherX * errorZ;
        const float zProduct = yawZ * errorX;
        const float reciprocal = 1.0f / determinant;
        yawStep = __builtin_fmaf(otherZ, errorX, -xProduct) * reciprocal;
        otherStep = __builtin_fmaf(yawX, errorZ, -zProduct) * reciprocal;
    } else {
        const float sumX = otherX + yawX;
        const float sumZ = otherZ + yawZ;
        constexpr float tiny = 9.999999960041972e-13f;
        yawStep = __builtin_fabsf(sumX) > tiny ? errorX / sumX : 0.0f;
        otherStep = __builtin_fabsf(sumZ) > tiny ? errorZ / sumZ : 0.0f;
        if (__builtin_fabsf(yawStep) < tiny && otherStep < tiny) return false;
    }
    return true;
}
}

// @ 0x822860D8
int BallShot_SolveTrajectory(void* entry, const Vec4* start, const Vec4* target,
    int /*unusedR6*/, Vec4* spin, int firstFlag, Vec4* velocity, int secondFlag,
    bool stackFlag, ballshot::SolveSample* sample, float speed, float angle) {
    g_shotSolveState = static_cast<int32_t>(static_cast<uint32_t>(g_shotSolveState) + 1u);
    if (g_shotSolveState > 128) {
        nop_8240E6D0("ComputePostHitVel called itself too many times.");
        velocity->x = 0.0f;
        velocity->y = 0.0f;
        velocity->z = start->z > target->z ? -speed : speed;
        return 0;
    }
    const float originalSpeed = speed;
    const float originalAngle = angle;
    const uint8_t firstByte = static_cast<uint8_t>(firstFlag);
    const uint8_t secondByte = static_cast<uint8_t>(secondFlag);
    const float dx = start->x - target->x;
    const float dz = start->z - target->z;
    const float xSquare = dx * dx;
    const float distance = static_cast<float>(crt_sqrt(__builtin_fmaf(dz, dz, xSquare)));
    float yaw = distance > 0.0000009999999974752427f
        ? static_cast<float>(crt_asin((target->x - start->x) / distance)) : 0.0f;
    const float maximumAngle = EntryMaxAngle(entry);
    float perturbationW = 0.0f;
    if (firstByte == 0 && sample == nullptr) {
        Vec4 raised = *target;
        if (secondByte == 0) raised.y += 1.0f;
        Vec4 difference{FlushVmx(FlushVmx(start->x) - FlushVmx(raised.x)),
                        FlushVmx(FlushVmx(start->y) - FlushVmx(raised.y)),
                        FlushVmx(FlushVmx(start->z) - FlushVmx(raised.z)),
                        FlushVmx(FlushVmx(start->w) - FlushVmx(raised.w))};
        const float squareLength = Dot3(difference, difference);
        const Vec4 inverse = RefinedInverseLength(squareLength);
        const float length = FlushVmx(squareLength * FlushVmx(inverse.x));
        perturbationW = FlushVmx(squareLength * FlushVmx(inverse.w));
        const float initial = static_cast<float>(crt_asin((raised.y - start->y) / length));
        const float excess = initial - maximumAngle;
        angle = excess >= 0.0f ? maximumAngle : initial;
    }
    const auto* initialTable = static_cast<const TrajectoryTable*>(g_pTableDims);
    const float ballHeight = initialTable->height + CurrentBallRadius();
    const float minimumAngle = firstByte == 0 && !(start->y > ballHeight)
        ? ph_Atan2fSafe(ballHeight - start->y, distance) : -1.5707963705062866f;
    const float derivativeScale = g_fastOrbitMul;
    constexpr float derivativeOffset = 0.10000000149011612f;
    constexpr float converged = 9.999999747378752e-05f;

    Vec4 candidate = *target;
    Vec4 bestVelocity = candidate;
    Vec4 result{}, probe{};
    ballshot::TrajectoryContacts contacts{};
    uint8_t bestFlags[3] = {1, 0, 0};
    float bestFirstMeasure = 0.0f, bestSecondMeasure = 0.0f;
    float bestSquare = 3.4028234663852886e+38f;
    float previousSquare = 100000000.0f;
    float yawStep = 0.0f, pitchStep = 0.0f, speedStep = 0.0f;
    int iterations = 0, backtracks = 0, stalls = 0;
    bool useBest = false;
    for (;;) {
        const float yawCosRaw = static_cast<float>(crt_cos(yaw));
        const float yawSin = static_cast<float>(crt_sin(yaw));
        const float pitchCos = static_cast<float>(crt_cos(angle));
        const float pitchSin = static_cast<float>(crt_sin(angle));
        const float yawCos = start->z > 0.0f ? -yawCosRaw : yawCosRaw;
        const float xFactor = pitchCos * yawSin;
        const float zFactor = pitchCos * yawCos;
        const float vertical = pitchSin * speed;
        candidate.x = xFactor * speed;
        candidate.y = vertical;
        candidate.z = zFactor * speed;
        contacts.flags[0] = 1;
        contacts.flags[1] = 0;
        contacts.flags[2] = 0;
        BallShot_SimulateTrajectory(entry, start, &candidate, spin, target, firstFlag,
                                   &result, stackFlag, &contacts);
        const float errorX = target->x - result.x;
        const float errorZ = target->z - result.z;
        const float zSquare = errorX * errorX;
        const float square = __builtin_fmaf(errorZ, errorZ, zSquare);
        if (!(square < previousSquare) && iterations != 0) {
            yawStep *= 0.5f;
            pitchStep *= 0.5f;
            speedStep *= 0.5f;
            yaw = WrapAngle(yaw - yawStep);
            angle = WrapAngle(angle - pitchStep);
            // Only the angular coordinates are backed out; speed is retained.
            if (backtracks == 0 && ++stalls > 4) { useBest = true; break; }
            if (++backtracks > 4) { useBest = true; break; }
        } else {
            if (square < bestSquare) {
                bestSquare = square;
                bestVelocity = candidate;
                bestFlags[0] = contacts.flags[0];
                bestFlags[1] = contacts.flags[1];
                bestFlags[2] = contacts.flags[2];
                bestFirstMeasure = contacts.firstMeasure;
                bestSecondMeasure = contacts.secondMeasure;
                if (square < converged) break;
            }
            const float shiftedYaw = WrapAngle(yaw + derivativeOffset);
            const float shiftedCosRaw = static_cast<float>(crt_cos(shiftedYaw));
            const float shiftedSin = static_cast<float>(crt_sin(shiftedYaw));
            const float shiftedCos = start->z > 0.0f ? -shiftedCosRaw : shiftedCosRaw;
            const float shiftedX = shiftedSin * pitchCos;
            const float shiftedZ = shiftedCos * pitchCos;
            Vec4 perturbed{shiftedX * speed, vertical, shiftedZ * speed, perturbationW};
            BallShot_SimulateTrajectory(entry, start, &perturbed, spin, target, firstFlag,
                                       &probe, stackFlag, nullptr);
            const float yawX = (probe.x - result.x) * derivativeScale;
            const float yawZ = (probe.z - result.z) * derivativeScale;
            const bool varyPitch = firstByte == 0 && sample == nullptr;
            if (varyPitch) {
                float shiftedPitchCos, shiftedPitchSin;
                rage::cosSin(&shiftedPitchCos, &shiftedPitchSin, WrapAngle(angle + derivativeOffset));
                const float pitchX = shiftedPitchCos * yawSin;
                const float pitchZ = shiftedPitchCos * yawCos;
                perturbed.x = pitchX * speed;
                perturbed.y = shiftedPitchSin * speed;
                perturbed.z = pitchZ * speed;
            } else {
                const float shiftedSpeed = speed + derivativeOffset;
                const float horizontal = shiftedSpeed * pitchCos;
                perturbed.x = horizontal * yawSin;
                perturbed.y = shiftedSpeed * pitchSin;
                perturbed.z = horizontal * yawCos;
            }
            BallShot_SimulateTrajectory(entry, start, &perturbed, spin, target, firstFlag,
                                       &probe, stackFlag, nullptr);
            const float otherX = (probe.x - result.x) * derivativeScale;
            const float otherZ = (probe.z - result.z) * derivativeScale;
            float otherStep;
            if (!SolveCorrection(yawX, yawZ, otherX, otherZ, errorX, errorZ, yawStep, otherStep)) {
                useBest = true;
                break;
            }
            yawStep = ClampStep(yawStep, -0.5f, 0.5f);
            if (varyPitch) {
                const float below = minimumAngle - angle;
                const float above = maximumAngle - angle;
                const float belowHalf = below + 0.5f;
                const float aboveHalf = above - 0.5f;
                const float lower = belowHalf >= 0.0f ? below : -0.5f;
                const float upper = aboveHalf >= 0.0f ? 0.5f : above;
                pitchStep = ClampStep(otherStep, lower, upper);
                yaw = WrapAngle(yaw + yawStep);
                angle = WrapAngle(angle + pitchStep);
            } else {
                const float negativeSpeed = -speed;
                const float aboveLower = negativeSpeed - (-5.0f);
                const float lower = aboveLower >= 0.0f ? negativeSpeed : -5.0f;
                speedStep = ClampStep(otherStep, lower, 5.0f);
                yaw = WrapAngle(yaw + yawStep);
                speed += speedStep;
            }
            previousSquare = square;
            backtracks = 0;
            ++iterations;
        }
        if (iterations >= 64) break;
    }
    if (useBest) candidate = bestVelocity;
    Vec4 adjusted = *target;
    if (bestFlags[1] != 0 && secondByte == 0) {
        const float radius = CurrentBallRadius();
        const auto* table = static_cast<const TrajectoryTable*>(g_pTableDims);
        const float halfWidth = __builtin_fmaf(table->width, 0.5f, radius);
        const float outerWidth = halfWidth + 0.0020000000949949026f;
        const float contactX = contacts.secondPosition.x;
        if (contactX >= halfWidth) adjusted.x = outerWidth;
        else if (contactX <= -halfWidth) adjusted.x = -outerWidth;
        else adjusted.x = contactX;
        const float halfDepth = __builtin_fmaf(table->depth, 0.5f, radius);
        const float outerDepth = halfDepth + 0.0020000000949949026f;
        const float contactZ = contacts.secondPosition.z;
        if (contactZ >= halfDepth) adjusted.z = outerDepth;
        else if (contactZ < -halfDepth) adjusted.z = -outerDepth;
        else adjusted.z = contactZ;
        const float xDistance = __builtin_fabsf(start->x - adjusted.x) * 2.0f;
        const float yDistance = (target->y - start->y) * 0.5f;
        const float aboveX = yDistance - xDistance;
        const float minimumDepth = aboveX >= 0.0f ? yDistance : xDistance;
        if (adjusted.z > 0.0f && adjusted.z > start->z - minimumDepth)
            adjusted.z = start->z - minimumDepth;
        else if (adjusted.z < 0.0f && adjusted.z < start->z + minimumDepth)
            adjusted.z = start->z + minimumDepth;
        if (sample == nullptr) {
            return BallShot_SolveTrajectory(entry, start, &adjusted, 0, spin, 0, velocity, 1,
                                             true, nullptr, originalSpeed, originalAngle);
        }
        sample->firstMeasure = bestFirstMeasure;
        sample->secondMeasure = bestSecondMeasure;
        sample->flags[0] = 0;
        sample->flags[1] = bestFlags[2];
        sample->target = adjusted;
        sample->velocity = candidate;
        *velocity = candidate;
        return 1;
    }
    if (firstByte != 0) {
        bool retryHigher = false;
        if (originalAngle < 0.0f) {
            if (sample == nullptr && bestFlags[2] != 0) {
                float retryAngle = 0.0f;
                if (bestFlags[0] != 0 && originalAngle >= -1.0799224376678467f)
                    retryAngle = originalAngle - 0.09817477315664291f;
                return BallShot_SolveTrajectory(entry, start, target, 0, spin, firstFlag, velocity,
                                                 secondByte, stackFlag, nullptr, speed, retryAngle);
            }
            retryHigher = bestFlags[0] == 0;
        } else if (originalAngle >= 0.0f) {
            retryHigher = bestFlags[2] != 0;
        }
        if (retryHigher) {
            const float increment = 0.09817477315664291f;
            if (sample == nullptr && originalAngle <= maximumAngle - increment) {
                const float next = originalAngle + increment;
                const float retryAngle = -next >= 0.0f ? 0.0f : next;
                return BallShot_SolveTrajectory(entry, start, target, 0, spin, firstFlag, velocity,
                                                 secondByte, stackFlag, nullptr, speed, retryAngle);
            }
            if (bestFlags[2] != 0 && __builtin_fabsf(target->z) > g_ambientCubeFalloff) {
                adjusted.x = target->x;
                adjusted.y = target->y;
                adjusted.z *= 0.75f;
                if (sample == nullptr) {
                    return BallShot_SolveTrajectory(entry, start, &adjusted, 0, spin, firstFlag,
                        velocity, secondByte, stackFlag, nullptr, speed, -0.09817477315664291f);
                }
            }
        }
        if (bestFlags[0] == 0) {
            const auto* table = static_cast<const TrajectoryTable*>(g_pTableDims);
            const float cushion = g_ballDragCoef;
            bool changed = false;
            const float halfWidth = table->width * 0.5f;
            const float contactX = contacts.firstPosition.x;
            if (__builtin_fabsf(contactX) > halfWidth) {
                const float boundary = contactX > 0.0f ? halfWidth - cushion : cushion - halfWidth;
                adjusted.x -= contactX - boundary;
                changed = true;
            }
            const float halfDepth = table->depth * 0.5f;
            const float contactZ = contacts.firstPosition.z;
            if (__builtin_fabsf(contactZ) > halfDepth) {
                const float boundary = contactZ > 0.0f ? halfDepth - cushion : cushion - halfDepth;
                adjusted.z -= contactZ - boundary;
                changed = true;
            } else if (NegativeSign(contactZ) != NegativeSign(start->z)) {
                adjusted.z -= contactZ;
                changed = true;
            }
            if (changed && sample == nullptr) {
                return BallShot_SolveTrajectory(entry, start, &adjusted, 0, spin, firstFlag,
                    velocity, secondByte, stackFlag, nullptr, originalSpeed, -0.09817477315664291f);
            }
        }
    } else if (sample != nullptr && bestFlags[2] != 0) {
        const auto* table = static_cast<const TrajectoryTable*>(g_pTableDims);
        const float height = (table->height + g_ballTableSurfaceOffset) + CurrentBallRadius();
        float correction = height - bestSecondMeasure;
        if (start->z > 0.0f) correction = -correction;
        adjusted.z += correction;
    }
    if (sample != nullptr) {
        sample->firstMeasure = bestFirstMeasure;
        sample->secondMeasure = bestSecondMeasure;
        sample->velocity = candidate;
        sample->target = adjusted;
        sample->flags[0] = bestFlags[1] == 0 && firstByte == bestFlags[0]
            && (firstByte == 0 || bestFlags[2] == 0);
        sample->flags[1] = bestFlags[2];
        *velocity = candidate;
        return 1;
    }
    *velocity = candidate;
    return iterations < 64 ? 1 : 0;
}
