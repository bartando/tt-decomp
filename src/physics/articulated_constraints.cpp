#include "articulated_constraints.hpp"
#include "articulated_joint.hpp"
#include <string.h>

extern "C" const float g_phZeroFloat; // @ 0x8202D110

// Flatten each child joint's scalar constraints. Error is suppressed when its
// sign differs from the current value's sign, including the sign bit of zero
// and NaNs; a numeric >= comparison would change the retail branch behavior.
// phArticulatedCollider_GatherJointLimits @ 0x82258C98 | size: 0x140
int32_t phArticulatedCollider_GatherJointLimits(void* jointData, uint32_t* jointIndices,
    uint32_t* states, float* errors, float* referenceErrors, float* weights) {
    uint32_t* data = static_cast<uint32_t*>(jointData);
    const int32_t jointCount = static_cast<int32_t>(data[1] - 1);
    int32_t total = 0;
    for (int32_t index = 0; index < jointCount; ++index) {
        auto* joint = reinterpret_cast<rage::phArticulatedJointOps*>(uintptr_t(data[42 + index]));
        const int32_t count = joint->GetConstraintCount();
        if (count <= 0)
            continue;
        const int32_t first = total;
        total += count;
        for (int32_t axis = 0; axis < count; ++axis) {
            const int32_t row = first + axis;
            jointIndices[row] = index;
            uint32_t state;
            float value, weight, limit, reference;
            joint = reinterpret_cast<rage::phArticulatedJointOps*>(uintptr_t(data[42 + index]));
            joint->GetConstraintState(axis, &state, &value, &weight, &limit, &reference);
            const float error = value - limit;
            states[row] = state;
            weights[row] = weight;
            errors[row] = error;
            uint32_t valueBits, errorBits;
            memcpy(&valueBits, &value, 4);
            memcpy(&errorBits, &error, 4);
            if ((valueBits ^ errorBits) & 0x80000000u)
                errors[row] = g_phZeroFloat;
            referenceErrors[row] = value - reference;
        }
    }
    return total;
}
