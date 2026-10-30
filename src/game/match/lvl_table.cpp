#include "game/lvl_table.hpp"

#include <cmath>
#include <cstring>

// VMX multiply/add instructions round the product before adding/subtracting.
#pragma clang fp contract(off)

extern "C" {
extern const uint32_t lbl_82619BE0[4]; // @ 0x82619BE0 — xyz mask, filled at startup
extern const float lbl_82619BD0[4];    // @ 0x82619BD0 — (0, 0, 0, 1), filled at startup
extern const float lbl_82619BF0[4];    // @ 0x82619BF0 — estimate sentinel, filled at startup
extern const float lbl_82606750[4];    // @ 0x82606750 — replacement for the sentinel
extern const float lbl_825CB7C0[4];    // @ 0x825CB7C0 — (1, 1, 1, 0)
extern const float lbl_825CB7D0[4];    // @ 0x825CB7D0 — (0.5, 0.5, 0.5, 0)
}

namespace {

float maskLane(float value, uint32_t mask, float extra = 0.0f) {
    uint32_t bits, extraBits;
    std::memcpy(&bits, &value, sizeof(bits));
    std::memcpy(&extraBits, &extra, sizeof(extraBits));
    bits = (bits & mask) | extraBits;
    std::memcpy(&value, &bits, sizeof(value));
    return value;
}

// vmsum3fp128/vmsum4fp128 accumulate the products before rounding to float.
float dot(const LvlTableVector& a, const LvlTableVector& b, int count) {
    double sum = 0.0;
    for (int i = 0; i < count; ++i)
        sum += static_cast<double>(a.lane[i]) * b.lane[i];
    return static_cast<float>(sum);
}

float flushVmx(float value) {
    uint32_t bits;
    std::memcpy(&bits, &value, sizeof(bits));
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        std::memcpy(&value, &bits, sizeof(value));
    }
    return value;
}

} // namespace

// @ 0x82337008
void lvlTable_7008_2h(const LvlTableMotionView* self, LvlTableVector* position, uint32_t mode,
                      const LvlTableVector& direction, const LvlTableVector& step, const LvlTableVector& origin) {
    auto* alignedPosition = reinterpret_cast<LvlTableVector*>(reinterpret_cast<uintptr_t>(position) & ~uintptr_t(15));
    const LvlTableVector initial = *alignedPosition;
    LvlTableVector result;
    for (int i = 0; i < 4; ++i)
        result.lane[i] = initial.lane[i] + direction.lane[i] * step.lane[i];

    if ((mode & 0xFFFF) == 1) {
        const LvlTableTransform& transform = self->transforms[self->transformIndices[self->activeTransform]];
        LvlTableVector point;
        for (int i = 0; i < 4; ++i)
            point.lane[i] = maskLane(result.lane[i], lbl_82619BE0[i], lbl_82619BD0[i]);

        // The merge instructions transpose the matrix. The fourth output lane
        // is point.x, left over from the final merge, rather than a fourth dot.
        LvlTableVector transformed;
        for (int i = 0; i < 3; ++i) {
            LvlTableVector column{{transform.row[0].lane[i], transform.row[1].lane[i],
                                   transform.row[2].lane[i], transform.row[3].lane[i]}};
            transformed.lane[i] = dot(point, column, 4);
        }
        transformed.lane[3] = point.lane[0];

        LvlTableVector relativeMotion;
        for (int i = 0; i < 4; ++i) {
            const float displacement = result.lane[i] - origin.lane[i];
            const float localDelta = result.lane[i] - transformed.lane[i];
            const float surfaceDelta = localDelta - self->motionOffset.lane[i];
            relativeMotion.lane[i] = displacement - surfaceDelta;
        }

        const float normalMotion = dot(relativeMotion, direction, 3);
        LvlTableVector tangent;
        for (int i = 0; i < 4; ++i)
            tangent.lane[i] = relativeMotion.lane[i] - direction.lane[i] * normalMotion;
        const float tangentSq = dot(tangent, tangent, 3);
        const float estimate = 1.0f / std::sqrt(tangentSq); // vrsqrtefp approximation

        for (int i = 0; i < 4; ++i) {
            const float zero = lbl_82606750[i];
            const float one = lbl_825CB7C0[i];
            const float y = estimate == lbl_82619BF0[i] ? zero : estimate;
            const float square = y * y;
            const float halfY = lbl_825CB7D0[i] * y;
            // vnmsub is -(product - addend), including the sign of zero.
            const float error = -(tangentSq * square - one);
            const float inverseLength = error * halfY + y;
            const float length = tangentSq * inverseLength;
            const float reciprocal = 1.0f / length; // vrefp, followed by one refinement
            const float reciprocalError = -(reciprocal * length - one);
            const float refinedReciprocal = reciprocal * reciprocalError + reciprocal;
            const float sliding = self->slidingResponse.lane[i] * tangent.lane[i];
            const float normalized = sliding * refinedReciprocal;
            const float linear = self->linearResponse.lane[i] * tangent.lane[i];
            const float limit = maskLane(self->threshold.lane[i], lbl_82619BE0[i], lbl_82619BD0[i]);
            const float correction = limit > maskLane(tangentSq, lbl_82619BE0[i]) ? linear : normalized;
            // vsel uses the comparison mask: negative normal motion selects one.
            const float enabled = zero > normalMotion ? one : zero;
            result.lane[i] = -(correction * enabled - result.lane[i]);
        }
    }

    *alignedPosition = result;
}

// @ 0x82337D28
uint32_t lvlTable_7D28_2h(int32_t count, const LvlTableVector* points, const uint32_t* indices,
                        uint32_t* output, const LvlTableVector& distanceLimitSq, const LvlTableVector& origin) {
    if (count <= 0)
        return 0;

    const auto* alignedPoints = reinterpret_cast<const LvlTableVector*>(
        reinterpret_cast<uintptr_t>(points) & ~uintptr_t(15));
    LvlTableVector center{}, limits;
    for (int lane = 0; lane < 3; ++lane)
        center.lane[lane] = flushVmx(origin.lane[lane]);
    for (int lane = 0; lane < 4; ++lane)
        limits.lane[lane] = flushVmx(distanceLimitSq.lane[lane]);
    uint32_t accepted = 0;
    // The original unrolls 32 candidates without a remainder path. Callers
    // supply whole batches; a positive partial batch still consumes 32.
    for (uint32_t batch = 0; batch < static_cast<uint32_t>(count); batch += 32) {
        for (uint32_t i = 0; i < 32; ++i) {
            const uint32_t index = indices[batch + i];
            // rlwinm discards the high four index bits before the vector load.
            const LvlTableVector& point = alignedPoints[index & 0x0FFFFFFFu];
            LvlTableVector delta{};
            for (int lane = 0; lane < 3; ++lane)
                delta.lane[lane] = flushVmx(flushVmx(point.lane[lane]) - center.lane[lane]);
            const float distanceSq = flushVmx(dot(delta, delta, 3));
            // CR6's all-true bit requires all four limits to be strictly greater
            // than the replicated xyz dot. Unordered comparisons reject.
            bool inside = true;
            for (int lane = 0; lane < 4; ++lane)
                inside &= limits.lane[lane] > distanceSq;

            // stwx is unconditional: a rejected candidate overwrites this slot,
            // including the slot just past the accepted prefix at return.
            output[accepted] = index;
            accepted += inside;
        }
    }
    return accepted;
}
