// One prediction step, including swept table/net contacts (0x82288368).
#include "ball_predict.hpp"
#include "ball_flight.hpp"

#include <cmath>
#include <stdint.h>

#pragma clang fp contract(off)

namespace predictionStep {
using Vec4 = BallFlightVec4;

struct Material { uint8_t _pad00[0xC]; float friction; };

struct alignas(16) Intersection {
    uint32_t count;
    uint8_t _pad04[12];
    Vec4 position;
    Vec4 normal;
    float fraction;
    float distance;
    uint32_t material;
    int32_t face;
    uint16_t child;
    uint16_t flags;
    uint8_t flag44;
    uint8_t _pad45;
    uint16_t surface; // 0: table, 1: net
};
static_assert(sizeof(Intersection) == 0x50, "sweep intersection layout");

struct Bound {
    virtual void ScalarDtor(int flags) = 0;
    virtual void Slot1() = 0;
    virtual void Slot2() = 0;
    virtual void Slot3() = 0;
    virtual void Slot4() = 0;
    virtual void Slot5() = 0;
    virtual void Slot6() = 0;
    virtual void Slot7() = 0;
    virtual void Slot8() = 0;
    virtual void Slot9() = 0;
    virtual void Slot10() = 0;
    virtual Material* GetMaterial(uint32_t index) = 0;
    virtual void Slot12() = 0;
    virtual void Slot13() = 0;
    virtual void Slot14() = 0;
    virtual void Slot15() = 0;
    virtual void Slot16() = 0;
    virtual void Slot17() = 0;
    virtual void Slot18() = 0;
    virtual void Slot19() = 0;
    virtual void Slot20() = 0;
    virtual void Slot21() = 0;
    // The two unused integer homes retain r8/r9 for the result and flags;
    // the Xenon caller never populates r6/r7 with meaningful arguments.
    virtual uint32_t Sweep(const Vec4* start, const Vec4* axis, uint32_t unusedR6,
                           uint32_t unusedR7, Intersection* result, uint32_t flags,
                           float radius, float length) = 0;
    uint32_t _04;
    float radius; // +0x08 on Xenon
};

struct Archetype { uint8_t _pad00[0xC]; Bound* bound; };
struct Instance { void* vtable; Archetype* archetype; };
struct Proxy { uint8_t _pad00[0x14]; Instance* instance; };
struct SceneOwner { uint8_t _pad00[0x7C]; Proxy* proxy; };
struct Scene { uint8_t _pad00[0x48]; SceneOwner* owner; };
struct Loop { uint8_t _pad00[0x208]; float frameRate; };
struct State {
    uint8_t _pad00[0x10];
    gdBallPredictData* banks[2];
    uint8_t _pad18[0x10];
    float samplePeriod;
};
struct Net { uint8_t _pad00[0x78]; float friction, elasticity; };
struct Table {
    Net* net;
    float friction;
    uint8_t _pad08[0xC];
    float height, length;
};
} // namespace predictionStep

extern int32_t g_currentInputSlot;                // @ 0x82606578
extern "C" uint8_t g_ballSplashArray[832];        // @ 0x8261A3D0
extern void* g_loop_obj_ptr;                      // @ 0x825EAB30
extern void* g_game_state_ptr;                    // @ 0x8271A2F8
extern void* lbl_82606564;                        // @ 0x82606564
extern void** g_ppBallInst;                       // @ 0x8271A2F4
extern void* g_pTableDims;                        // @ 0x8271A304
extern "C" float g_ballDragCoef;                 // @ 0x825C8078
extern "C" float g_phCapsuleShapeK;              // @ 0x825C8080
extern "C" float g_identityVector[4];            // @ 0x82606740
extern "C" const float lbl_82619BF0[4];          // @ 0x82619BF0
extern "C" const float lbl_82606750[4];          // @ 0x82606750
extern "C" const float lbl_825CB7C0[4];          // @ 0x825CB7C0
extern "C" const float lbl_825CB7D0[4];          // @ 0x825CB7D0
extern double crt_sqrt(double value);             // @ 0x824301D0
extern double crt_acos(double value);             // @ 0x82430E90
extern double crt_cos(double value);              // @ 0x824302B0
extern double crt_sin(double value);              // @ 0x824301D8
extern void nop_8240E6D0(const char* format, ...);  // @ 0x8240E6D0

namespace {
using namespace predictionStep;

float Flush(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, 4);
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, 4);
    }
    return value;
}
uint32_t Bits(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, 4);
    return bits;
}
Vec4 Scale(const Vec4& v, float factor) {
    return {Flush(Flush(v.x) * Flush(factor)), Flush(Flush(v.y) * Flush(factor)),
            Flush(Flush(v.z) * Flush(factor)), Flush(Flush(v.w) * Flush(factor))};
}
Vec4 Add(const Vec4& a, const Vec4& b) {
    return {Flush(Flush(a.x) + Flush(b.x)), Flush(Flush(a.y) + Flush(b.y)),
            Flush(Flush(a.z) + Flush(b.z)), Flush(Flush(a.w) + Flush(b.w))};
}
Vec4 Sub(const Vec4& a, const Vec4& b) {
    return {Flush(Flush(a.x) - Flush(b.x)), Flush(Flush(a.y) - Flush(b.y)),
            Flush(Flush(a.z) - Flush(b.z)), Flush(Flush(a.w) - Flush(b.w))};
}
Vec4 Nmsub(const Vec4& a, float factor, const Vec4& c) {
    const Vec4 difference = Sub(Scale(a, factor), c);
    return {Flush(-difference.x), Flush(-difference.y), Flush(-difference.z), Flush(-difference.w)};
}
float Dot3(const Vec4& v) {
    double sum = static_cast<double>(Flush(v.x)) * Flush(v.x);
    sum += static_cast<double>(Flush(v.y)) * Flush(v.y);
    sum += static_cast<double>(Flush(v.z)) * Flush(v.z);
    return Flush(static_cast<float>(sum));
}
Vec4 InverseLength3(const Vec4& v) {
    const float lengthSq = Dot3(v);
    const float estimate = Flush(static_cast<float>(1.0 / __builtin_sqrt(static_cast<double>(lengthSq))));
    Vec4 result;
    float* out = &result.x;
    for (int i = 0; i < 4; ++i) {
        const float y = estimate == Flush(lbl_82619BF0[i]) ? lbl_82606750[i] : estimate;
        const float square = Flush(Flush(y) * Flush(y));
        const float half = Flush(Flush(lbl_825CB7D0[i]) * Flush(y));
        const float error = Flush(-Flush(Flush(lengthSq * square) - Flush(lbl_825CB7C0[i])));
        out[i] = Flush(Flush(error * half) + Flush(y));
    }
    return result;
}
Vec4 Normalize3(const Vec4& v) {
    const Vec4 inverse = InverseLength3(v);
    return {Flush(Flush(v.x) * Flush(inverse.x)), Flush(Flush(v.y) * Flush(inverse.y)),
            Flush(Flush(v.z) * Flush(inverse.z)), Flush(Flush(v.w) * Flush(inverse.w))};
}
const BallFlightShotView* Shot() {
    const uint32_t offset = static_cast<uint32_t>(g_currentInputSlot) * 0x1A0u;
    return reinterpret_cast<const BallFlightShotView*>(g_ballSplashArray + offset);
}
State* CurrentState() { return static_cast<State*>(g_game_state_ptr); }
Table* CurrentTable() { return static_cast<Table*>(g_pTableDims); }
}

// @ 0x82288368
void BallPredict_StepSample(gdBallPredictSample* sample, int bank) {
    using namespace predictionStep;
    alignas(16) Vec4 velocity, spin, position;
    __builtin_memcpy(&velocity, &sample->vel, 16);
    __builtin_memcpy(&spin, &sample->angVel, 16);
    alignas(16) Vec4 acceleration;
    BallFlight_Acceleration(&acceleration, Shot(), &velocity, &spin);

    const float rate = static_cast<Loop*>(g_loop_obj_ptr)->frameRate + 0.5f;
    float step = 1.0f / static_cast<float>(static_cast<int32_t>(rate));
    float predictionStep = CurrentState()->samplePeriod;
    const uint32_t oldSign = Bits(velocity.z) >> 31;
    velocity = Add(Scale(acceleration, step), velocity);
    if ((Bits(velocity.z) >> 31) != oldSign) velocity.z = 0.0f;
    __builtin_memcpy(&position, &sample->pos, 16);
    alignas(16) Vec4 end = Add(Scale(velocity, step), position);
    alignas(16) Vec4 axis = Sub(end, position);
    const float displacementSq = Dot3(axis);

    Bound* tableBound = static_cast<Scene*>(lbl_82606564)->owner->proxy->instance->archetype->bound;
    Intersection hit{};
    __builtin_memcpy(&hit.position, g_identityVector, 16);
    __builtin_memcpy(&hit.normal, g_identityVector, 16);
    hit.face = -1;
    hit.child = 0xFFFF;
    float length = 0.0f;
    if (displacementSq > 1e-12f) {
        const float distance = static_cast<float>(crt_sqrt(displacementSq));
        length = distance + 0.001f;
        axis = Scale(axis, length / distance);
    } else {
        const float speedSq = Dot3(velocity);
        if (speedSq > 1e-12f) {
            length = 0.001f;
            const float inverse = speedSq == 0.0f ? 0.0f : 1.0f / __builtin_sqrtf(speedSq);
            axis = Scale(velocity, inverse * 0.001f);
        }
    }
    auto* ball = static_cast<Instance*>(*g_ppBallInst);
    const float radius = ball ? ball->archetype->bound->radius : 0.0f;
    bool tableBounce = false;
    bool netBounce = false;
    if (length > 0.0f) {
        alignas(16) Vec4 start = Sub(end, axis);
        const float limit = __builtin_fmaf(CurrentTable()->length, 0.5f, radius) + g_ballDragCoef;
        if (__builtin_fabsf(start.z) < limit || __builtin_fabsf(end.z) < limit) {
            if (sample->flag9 != 0 && axis.y < 0.0f &&
                end.y < radius + CurrentTable()->height && start.y > CurrentTable()->height &&
                start.y < (radius + CurrentTable()->height) + 0.001f) {
                start.y = (radius + CurrentTable()->height) + 0.001f;
                axis = Sub(end, start);
                length = Flush(Dot3(axis) * InverseLength3(axis).x);
            }
            const uint32_t collided = tableBound->Sweep(&start, &axis, 0, 0, &hit, 1, radius, length);
            if (static_cast<uint8_t>(collided) != 0) {
                float friction = 0.0f;
                float elasticity = 0.0f;
                Table* table = nullptr;
                if (hit.surface == 0) {
                    if (hit.normal.y > 0.0f) {
                        tableBounce = true;
                        const float cornerAngle = *reinterpret_cast<const float*>(
                            CurrentState()->banks[1]->m_shot + 0x80);
                        if (hit.normal.y < 1.0f && __builtin_fabsf(cornerAngle) > 1e-6f) {
                            const float x = hit.normal.x;
                            const float z = hit.normal.z;
                            const float squareX = x * x;
                            const float horizontalSq = __builtin_fmaf(z, z, squareX);
                            if (horizontalSq > 1e-6f) {
                                const float tilt = cornerAngle * 0.01745329238474369f;
                                const float angle = static_cast<float>(crt_acos(hit.normal.y)) + tilt;
                                hit.normal.y = static_cast<float>(crt_cos(angle));
                                const float sine = static_cast<float>(crt_sin(angle));
                                const float inverse = horizontalSq == 0.0f ? 0.0f : 1.0f / __builtin_sqrtf(horizontalSq);
                                const float scale = sine * inverse;
                                hit.normal.x = x * scale;
                                hit.normal.z = z * scale;
                                hit.normal = Normalize3(hit.normal);
                            }
                        }
                    }
                    auto* currentBall = static_cast<Instance*>(*g_ppBallInst);
                    Material* material = currentBall->archetype->bound->GetMaterial(0);
                    table = CurrentTable();
                    elasticity = Shot()->elasticity;
                    friction = material->friction * table->friction;
                    if (elasticity == 0.949999988079071f) friction = 0.10000000149011612f;
                } else {
                    table = CurrentTable();
                    if (hit.surface == 1) {
                        netBounce = true;
                        friction = table->net->friction;
                    }
                }
                if (netBounce) {
                    friction = table->net->friction;
                    elasticity = table->net->elasticity;
                    nop_8240E6D0("\nCollided with net. Sample pos x:%f, y:%f, z:%f",
                                 static_cast<double>(sample->pos.x), static_cast<double>(sample->pos.y),
                                 static_cast<double>(sample->pos.z));
                    if (__builtin_fabsf(sample->pos.z) > table->length * g_phCapsuleShapeK &&
                        __builtin_fabsf(axis.z) < g_phCapsuleShapeK) {
                        nop_8240E6D0("\n\nstart: %f %f %f", static_cast<double>(start.x), static_cast<double>(start.y), static_cast<double>(start.z));
                        nop_8240E6D0("\naxis: %f %f %f", static_cast<double>(axis.x), static_cast<double>(axis.y), static_cast<double>(axis.z));
                        nop_8240E6D0("\nradius: %f", static_cast<double>(radius));
                        nop_8240E6D0("\nlength: %f", static_cast<double>(length));
                        nop_8240E6D0("\n\nPlease send these numbers to Nathan Carlin\n");
                    }
                }
                if (netBounce || tableBounce) {
                    if (displacementSq > 1e-12f) {
                        const float distance = static_cast<float>(crt_sqrt(displacementSq));
                        const float remaining = 1.0f - hit.fraction;
                        const float extension = (0.001f / distance) + 1.0f;
                        const float fraction = -__builtin_fmaf(extension, remaining, -1.0f);
                        const float correction = (1.0f - fraction) * step;
                        end = Nmsub(velocity, correction, end);
                        velocity = Nmsub(acceleration, correction, velocity);
                    }
                    BallFlight_Bounce(Shot(), &hit.normal, &end, &velocity, &spin, radius, friction, elasticity);
                    const double lower = hit.fraction >= 0.0f ? hit.fraction : 0.0;
                    const double fraction = lower - 1.0 >= 0.0 ? 1.0 : lower;
                    const float remainder = (1.0f - static_cast<float>(fraction)) * step;
                    const float contactedStep = step - remainder;
                    predictionStep = (contactedStep / step) * predictionStep;
                    step = contactedStep;
                }
            }
        }
    }
    if (sample->bounced != 0 && tableBounce) {
        nop_8240E6D0("Adjacent samples are being marked as BounceTable");
    }
    __builtin_memcpy(&sample->vel, &velocity, 16);
    sample->bounced = static_cast<uint8_t>(tableBounce);
    sample->flag9 = static_cast<uint8_t>(netBounce);
    __builtin_memcpy(&sample->pos, &end, 16);
    __builtin_memcpy(&sample->angVel, &spin, 16);
    if (tableBounce || sample->pos.y <= radius) {
        sample->hittable = 0;
    } else {
        gdBallPredictData* data = CurrentState()->banks[bank];
        if (data->m_count != 0) {
            const gdBallPredictSample& previous = data->At(data->m_count - 1);
            if (previous.hittable != 0 && previous.bounced == 0) sample->hittable = 1;
        }
    }
    sample->time += predictionStep;
    sample->time2 += step;
}
