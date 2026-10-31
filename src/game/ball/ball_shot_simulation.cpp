// Simulate a candidate shot through its first table contact and optional bounce.
#include "ball_shot_solve.hpp"
#include <stdint.h>

#pragma clang fp contract(off)

namespace shotSimulation {
using Vec4 = BallFlightVec4;
struct Material { uint8_t _pad00[0x0C]; float friction; };
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
    uint32_t _04;
    float radius;                         // +0x08 on Xenon
};
struct Archetype { uint8_t _pad00[0x0C]; Bound* bound; };
struct Instance { void* vtable; Archetype* archetype; };
struct Net {
    uint8_t _pad00[0x80];
    float height, scaledHeight;
};
struct Table {
    Net* net;
    float friction;
    uint8_t _pad08[8];
    float width, height, depth;
};
struct Loop { uint8_t _pad00[0x208]; float frameRate; };
}

extern void* g_input_obj_ptr;                      // @ 0x825EAB28
extern void* g_loop_obj_ptr;                       // @ 0x825EAB30
extern void* g_pTableDims;                         // @ 0x8271A304
extern void** g_ppBallInst;                        // @ 0x8271A2F4
extern "C" int32_t lbl_825C9A2C;                  // @ 0x825C9A2C
extern "C" uint8_t lbl_825C5EC8[];                // @ 0x825C5EC8
extern "C" float g_ballTableSurfaceOffset;        // @ 0x826064B8
extern "C" float g_ballDragCoef;                  // @ 0x825C8078: table-edge clearance
extern "C" const BallFlightVec4 g_ballTableNormal; // @ 0x825CB7A0
extern int io_Input_poll_9D68(void* input);          // @ 0x821C9D68

namespace {
using namespace shotSimulation;
float SimFlush(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, 4);
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, 4);
    }
    return value;
}
bool SimSign(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, 4);
    return (bits >> 31) != 0;
}
Vec4 SimScale(const Vec4& value, float scale) {
    return {SimFlush(SimFlush(value.x) * SimFlush(scale)), SimFlush(SimFlush(value.y) * SimFlush(scale)),
            SimFlush(SimFlush(value.z) * SimFlush(scale)), SimFlush(SimFlush(value.w) * SimFlush(scale))};
}
Vec4 SimAdd(const Vec4& a, const Vec4& b) {
    return {SimFlush(SimFlush(a.x) + SimFlush(b.x)), SimFlush(SimFlush(a.y) + SimFlush(b.y)),
            SimFlush(SimFlush(a.z) + SimFlush(b.z)), SimFlush(SimFlush(a.w) + SimFlush(b.w))};
}
Vec4 SimNmsub(const Vec4& value, float scale, const Vec4& addend) {
    const Vec4 product = SimScale(value, scale);
    return {SimFlush(-SimFlush(product.x - SimFlush(addend.x))),
            SimFlush(-SimFlush(product.y - SimFlush(addend.y))),
            SimFlush(-SimFlush(product.z - SimFlush(addend.z))),
            SimFlush(-SimFlush(product.w - SimFlush(addend.w)))};
}
void SimStep(Vec4& position, Vec4& velocity, const Vec4& acceleration, float step) {
    velocity = SimAdd(SimScale(acceleration, step), velocity);
    position = SimAdd(SimScale(velocity, step), position);
}
int32_t SimTruncateFrameCount(float value) {
    if (value != value || value <= -2147483648.0f) return INT32_MIN;
    if (value >= 2147483648.0f) return INT32_MAX;
    return static_cast<int32_t>(value);
}
void SimMaxHeight(ballshot::TrajectoryContacts* contacts, float height) {
    const float difference = contacts->firstMeasure - height;
    contacts->firstMeasure = difference >= 0.0f ? contacts->firstMeasure : height;
}
bool SimCrossedEdge(const Vec4& previous, const Vec4& current, float halfWidth, float halfDepth) {
    const bool wasOutsideX = __builtin_fabsf(previous.x) > halfWidth;
    const bool isInsideX = __builtin_fabsf(current.x) < halfWidth;
    const bool wasOutsideZ = __builtin_fabsf(previous.z) > halfDepth;
    const bool isInsideZ = __builtin_fabsf(current.z) < halfDepth;
    return (wasOutsideX && isInsideX && (!wasOutsideZ || isInsideZ)) ||
           (wasOutsideZ && isInsideZ && (!wasOutsideX || isInsideX));
}
}

// @ 0x822823E0
bool BallShot_IsLocalPlay() {
    return static_cast<uint8_t>(io_Input_poll_9D68(g_input_obj_ptr)) == 0 && lbl_825C9A2C == 0;
}

// @ 0x82284010
void BallShot_RecordNetCrossing(ballshot::TrajectoryContacts* contacts,
    const BallFlightVec4* current, const BallFlightVec4* previous, float netHeight) {
    if (contacts == nullptr || SimSign(current->z) == SimSign(previous->z)) return;
    if (current->y < netHeight || previous->y < netHeight) {
        contacts->flags[2] = 1;
        contacts->secondMeasure = current->y;
    }
}

// @ 0x82284078
void BallShot_SimulateTrajectory(void* entry, const BallFlightVec4* start,
    const BallFlightVec4* launch, const BallFlightVec4* inputSpin, const BallFlightVec4* target,
    int firstFlag, BallFlightVec4* result, int stackFlag, ballshot::TrajectoryContacts* contacts) {
    using namespace shotSimulation;
    alignas(16) Vec4 position = *start;
    alignas(16) Vec4 velocity = *launch;
    alignas(16) Vec4 spin = *inputSpin;
    auto** const ballSlot = g_ppBallInst;
    auto* const table = static_cast<Table*>(g_pTableDims);
    const float halfDepth = table->depth * 0.5f;
    const float halfWidth = table->width * 0.5f;
    const float rate = static_cast<Loop*>(g_loop_obj_ptr)->frameRate + 0.5f;
    const float step = 1.0f / static_cast<float>(SimTruncateFrameCount(rate));
    auto* const initialBall = static_cast<Instance*>(*ballSlot);
    const float radius = initialBall ? initialBall->archetype->bound->radius : 0.0f;
    float netOffset;
    if (lbl_825C5EC8[0x30] != 0 && static_cast<uint8_t>(BallShot_IsLocalPlay()) != 0)
        netOffset = table->net->scaledHeight;
    else
        netOffset = table->net->height;
    const float netHeight = (table->height + netOffset) + g_ballTableSurfaceOffset;
    const bool outsideTarget = static_cast<uint8_t>(stackFlag) != 0 && __builtin_fabsf(target->z) > halfDepth;
    auto* const heightBall = static_cast<Instance*>(*ballSlot);
    const float heightRadius = heightBall ? heightBall->archetype->bound->radius : 0.0f;
    const float tableHeight = heightRadius + table->height;
    bool trackEntry = contacts != nullptr && start->y < tableHeight && !outsideTarget &&
        (__builtin_fabsf(start->z) > halfDepth || __builtin_fabsf(start->x) > halfWidth);
    float elapsed = 0.0f;
    alignas(16) Vec4 previous{};
    alignas(16) Vec4 acceleration{};
    const auto* shot = static_cast<const BallFlightShotView*>(entry);
    while ((position.y > tableHeight || velocity.y > 0.0f) && elapsed < 24.0f &&
           (!outsideTarget || position.y < tableHeight)) {
        BallFlight_Acceleration(&acceleration, shot, &velocity, &spin);
        previous = position;
        elapsed += step;
        SimStep(position, velocity, acceleration, step);
        if (contacts != nullptr) {
            if (SimSign(previous.z) != SimSign(position.z) &&
                (position.y < netHeight || previous.y < netHeight)) {
                contacts->secondMeasure = position.y;
                contacts->flags[2] = 1;
            }
            SimMaxHeight(contacts, position.y);
        }
        if (trackEntry) {
            if (previous.y < tableHeight && SimCrossedEdge(previous, position, halfWidth, halfDepth)) {
                contacts->flags[1] = 1;
                contacts->secondPosition = previous;
                trackEntry = false;
            } else if (position.y >= tableHeight) {
                contacts->flags[1] = 0;
                trackEntry = false;
            }
        }
    }
    if (!(position.y <= tableHeight && previous.y > tableHeight)) {
        *result = position;
        return;
    }
    const float correction = velocity.y < -0.0000009999999974752427f
        ? (position.y - tableHeight) / velocity.y : 0.0f;
    position = SimNmsub(velocity, correction, position);
    if (static_cast<uint8_t>(firstFlag) == 0) {
        *result = position;
        return;
    }
    if (contacts != nullptr) {
        contacts->firstPosition = position;
        auto* currentTable = static_cast<Table*>(g_pTableDims);
        const float depth = currentTable->depth * 0.5f;
        const float width = currentTable->width;
        const float clearance = g_ballDragCoef;
        contacts->flags[0] = SimSign(position.z) == SimSign(start->z) &&
            __builtin_fabsf(position.z) <= depth - clearance &&
            __builtin_fabsf(position.x) <= __builtin_fmaf(width, 0.5f, -clearance);
    }
    velocity = SimNmsub(acceleration, correction, velocity);
    auto* ball = static_cast<Instance*>(*g_ppBallInst);
    Material* material = ball->archetype->bound->GetMaterial(0);
    auto* currentTable = static_cast<Table*>(g_pTableDims);
    float elasticity;
    __builtin_memcpy(&elasticity, static_cast<const uint8_t*>(entry) + 0xBC, 4);
    const float friction = material->friction * currentTable->friction;
    BallFlight_Bounce(shot, &g_ballTableNormal, &position, &velocity, &spin, radius, friction, elasticity);
    BallFlight_Acceleration(&acceleration, shot, &velocity, &spin);
    SimStep(position, velocity, acceleration, correction);
    BallShot_RecordNetCrossing(contacts, &position, &previous, netHeight);
    while ((position.y > tableHeight || velocity.y > 0.0f) && elapsed < 24.0f) {
        BallFlight_Acceleration(&acceleration, shot, &velocity, &spin);
        previous = position;
        elapsed += step;
        SimStep(position, velocity, acceleration, step);
        if (contacts != nullptr) {
            if (SimSign(previous.z) != SimSign(position.z) &&
                (position.y < netHeight || previous.y < netHeight)) {
                contacts->secondMeasure = position.y;
                contacts->flags[2] = 1;
            }
            SimMaxHeight(contacts, position.y);
        }
    }
    const float finalCorrection = (position.y - tableHeight) / velocity.y;
    *result = SimNmsub(velocity, finalCorrection, position);
}
