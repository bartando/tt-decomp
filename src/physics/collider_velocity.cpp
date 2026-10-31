#include "collider_velocity.hpp"
#include "rage/ptr32.hpp"
#include <cmath>
#include <cstring>

extern const float g_floatOne; // @ 0x8202D108
extern const float g_floatZero; // @ 0x8202D110
extern "C" const float lbl_82606750[4]; // @ 0x82606750

namespace {
float flush(float value) {
    uint32_t bits;
    std::memcpy(&bits, &value, 4);
    if ((bits & 0x7f800000u) == 0) {
        bits &= 0x80000000u;
        std::memcpy(&value, &bits, 4);
    }
    return value;
}
float dot3(const float* a, const float* b) {
    double sum = 0.0;
    for (unsigned i = 0; i < 3; ++i)
        sum += double(flush(a[i])) * flush(b[i]);
    return flush(float(sum));
}
float* field(void* object, unsigned offset) {
    return reinterpret_cast<float*>(static_cast<uint8_t*>(object) + offset);
}
phColliderMotionOps* ops(void* object) {
    return static_cast<phColliderMotionOps*>(object);
}
void identity(float* matrix) {
    // W lanes of the basis are deliberately untouched.
    for (unsigned row = 0; row < 3; ++row)
        for (unsigned col = 0; col < 3; ++col)
            matrix[row * 4 + col] = row == col ? g_floatOne : g_floatZero;
    std::memset(matrix + 12, 0, 16);
}
void clampSpeed(void* collider, unsigned velocityOffset, unsigned momentumOffset,
                unsigned limitOffset) {
    float* velocity = field(collider, velocityOffset);
    const float limit = *field(collider, limitOffset);
    const float limitSquared = limit * limit;
    const float speedSquared = dot3(velocity, velocity);
    // PPC ble also exits for an unordered comparison.
    if (!(speedSquared > limitSquared)) return;
    float reciprocal = g_floatZero;
    if (speedSquared != g_floatZero)
        reciprocal = g_floatOne / std::sqrt(speedSquared);
    const float scale = limit * reciprocal;
    float scaled[4];
    for (unsigned i = 0; i < 4; ++i)
        scaled[i] = flush(flush(velocity[i]) * flush(scale));
    std::memcpy(velocity, scaled, 16);
    float* momentum = field(collider, momentumOffset);
    for (unsigned i = 0; i < 4; ++i)
        scaled[i] = flush(flush(momentum[i]) * flush(scale));
    std::memcpy(momentum, scaled, 16);
}
struct ResetStateOps {
    virtual void ReservedSlot0() = 0;
    virtual void Reset() = 0;
};
}

// @ 0x822CABE0
void phCollider_Reset(void* collider) {
    auto* bytes = static_cast<uint8_t*>(collider);
    identity(field(collider, 0xa0));
    std::memset(bytes + 0x1a0, 0, 16);
    ops(collider)->ClearForces();
    if (rage::load_ptr32<void>(collider, 0x10))
        ops(collider)->SynchronizeTransform();
    else
        identity(field(collider, 0x20));
    *field(collider, 0x1b0) = g_floatZero;
    bytes[0x1bc] = 0;
    *reinterpret_cast<uint32_t*>(bytes + 0x1b4) = 0;
    *reinterpret_cast<uint32_t*>(bytes + 0x1b8) = 0;
    *reinterpret_cast<uint32_t*>(bytes + 0x1c0) = 0;
    auto* state = rage::load_ptr32<uint8_t>(collider, 0x60);
    if (state) {
        state[0x14] = 0;
        *reinterpret_cast<uint32_t*>(state + 0x0c) = 13;
        *reinterpret_cast<uint32_t*>(state + 0x10) = 18;
        reinterpret_cast<ResetStateOps*>(state)->Reset();
    }
}

// @ 0x822CAE18
void phCollider_ClampLinearSpeed(void* collider) {
    clampSpeed(collider, 0xe0, 0x100, 0x90);
}

// @ 0x822CAEA8
void phCollider_ClampAngularSpeed(void* collider) {
    clampSpeed(collider, 0xf0, 0x110, 0x94);
}

// @ 0x822CCD28
void phCollider_SetAngularVelocity(void* collider, const float* velocity) {
    std::memmove(field(collider, 0xf0), velocity, 16);
    alignas(16) float inertia[16];
    ops(collider)->GetInertia(inertia, 0);
    // The virtual may replace velocity in the object: reload after the call.
    float angular[4];
    std::memcpy(angular, field(collider, 0xf0), 16);
    float momentum[4];
    for (unsigned col = 0; col < 3; ++col) {
        float column[3] = {inertia[col], inertia[4 + col], inertia[8 + col]};
        momentum[col] = dot3(angular, column);
    }
    momentum[3] = momentum[0];
    std::memcpy(field(collider, 0x110), momentum, 16);
}

// @ 0x822CCDF0
void phCollider_RefreshLinearVelocity(void* collider) {
    const float inverseMass = *field(collider, 0x68);
    float momentum[4], velocity[4];
    std::memcpy(momentum, field(collider, 0x100), 16);
    for (unsigned i = 0; i < 4; ++i)
        velocity[i] = flush(flush(momentum[i]) * flush(inverseMass));
    std::memcpy(field(collider, 0xe0), velocity, 16);
    ops(collider)->OnLinearVelocityChanged();
    phCollider_ClampLinearSpeed(collider);
}

// @ 0x822CCE58
void phCollider_RefreshAngularVelocity(void* collider) {
    float angular[4], basis[16], diagonal[4];
    std::memcpy(angular, field(collider, 0x110), 16);
    std::memcpy(basis, field(collider, 0xa0), 64);
    std::memcpy(diagonal, field(collider, 0x80), 16);
    float local[4];
    for (unsigned row = 0; row < 3; ++row)
        local[row] = dot3(basis + row * 4, angular);
    local[3] = local[0];
    for (unsigned i = 0; i < 4; ++i)
        local[i] = flush(flush(local[i]) * flush(diagonal[i]));
    float velocity[4];
    for (unsigned col = 0; col < 3; ++col) {
        float column[3] = {basis[col], basis[4 + col], basis[8 + col]};
        velocity[col] = dot3(local, column);
    }
    velocity[3] = velocity[0];
    std::memcpy(field(collider, 0xf0), velocity, 16);
    ops(collider)->OnAngularVelocityChanged();
    phCollider_ClampAngularSpeed(collider);
}

// @ 0x822CB680
void phCollider_PublishTransform(void* collider) {
    auto* instance = rage::load_ptr32<uint8_t>(collider, 0x10);
    auto* archetype = rage::load_ptr32<void>(instance, 4);
    auto* bound = rage::load_ptr32<uint8_t>(archetype, 0x0c);
    float matrix[16];
    std::memcpy(matrix, field(collider, 0xa0), 64);
    if (bound[6]) {
        float center[4];
        std::memcpy(center, bound + 0x50, 16);
        float displacement[4];
        for (unsigned col = 0; col < 3; ++col) {
            float column[3] = {matrix[col], matrix[4 + col], matrix[8 + col]};
            displacement[col] = dot3(center, column);
        }
        displacement[3] = displacement[0];
        for (unsigned i = 0; i < 4; ++i) {
            const float correction = flush(flush(lbl_82606750[i]) - flush(displacement[i]));
            matrix[12 + i] = flush(flush(matrix[12 + i]) + correction);
        }
    }
    std::memcpy(instance + 0x10, matrix, 64);
}
