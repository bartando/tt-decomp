#include "game/lvl_table.hpp"

#include <cmath>
#include <cstring>

// Keep separate arithmetic steps from contracting; fused lifts use __builtin_fmaf.
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

// Builtin copies keep the bit casts inline in freestanding builds too.
float maskLane(float value, uint32_t mask, float extra = 0.0f) {
    uint32_t bits, extraBits;
    __builtin_memcpy(&bits, &value, sizeof(bits));
    __builtin_memcpy(&extraBits, &extra, sizeof(extraBits));
    bits = (bits & mask) | extraBits;
    __builtin_memcpy(&value, &bits, sizeof(value));
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
    __builtin_memcpy(&bits, &value, sizeof(bits));
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, sizeof(value));
    }
    return value;
}

} // namespace

// @ 0x82340900 | size: 0x4B8 | formerly pongCreatureInst_0900
// Called from cloth simulation at 0x82341600 and 0x82341A50, after the sibling
// positional/attachment pass at 0x82340DB8. This is an inferred descriptive name.
void clothSolveDistanceConstraints(int32_t count, LvlTableVector* positions,
                                   const ClothDistanceConstraint* constraints, float relaxation) {
    if (count <= 0)
        return;

    auto* points = reinterpret_cast<LvlTableVector*>(reinterpret_cast<uintptr_t>(positions) & ~uintptr_t(15));
    const float strength = flushVmx(relaxation);
    for (uint32_t batch = 0; batch < static_cast<uint32_t>(count); batch += 8) {
        ClothDistanceConstraint records[8];
        LvlTableVector first[8], second[8];
        // The VMX loop snapshots all eight pairs, including duplicate endpoints.
        // Stores then run first/second, in record order; the last duplicate wins.
        for (uint32_t i = 0; i < 8; ++i) {
            records[i] = constraints[batch + i];
            first[i] = points[records[i].firstParticle];
            second[i] = points[records[i].secondParticle];
        }
        for (uint32_t i = 0; i < 8; ++i) {
            const ClothDistanceConstraint& record = records[i];
            LvlTableVector delta{};
            for (int lane = 0; lane < 3; ++lane)
                delta.lane[lane] = flushVmx(flushVmx(first[i].lane[lane]) - flushVmx(second[i].lane[lane]));

            const float distanceSq = flushVmx(dot(delta, delta, 3));
            const float restSq = flushVmx(record.restLengthSq);
            const float weight = flushVmx(record.firstWeight);
            const float firstStrength = flushVmx(weight * strength);
            const float secondStrength = flushVmx(flushVmx(1.0f - weight) * strength);
            const float compression = flushVmx(record.compressionScale);
            const float scale = restSq > distanceSq ? compression : 1.0f;
            const float negativeFirst = flushVmx(0.0f - flushVmx(firstStrength * scale));
            const float positiveSecond = flushVmx(secondStrength * scale);
            // vrefp has no scalar Newton refinement here. Division represents
            // its estimate; exact Xenon estimate bits remain unverified.
            const float inverseSum = flushVmx(1.0f / flushVmx(restSq + distanceSq));
            const float twiceRest = flushVmx(restSq + restSq);
            const float ratio = flushVmx(inverseSum * twiceRest);
            const float error = flushVmx(1.0f - ratio);
            const float firstCorrection = flushVmx(error * negativeFirst);
            const float secondCorrection = flushVmx(error * positiveSecond);
            LvlTableVector newFirst = first[i], newSecond = second[i];
            for (int lane = 0; lane < 3; ++lane) {
                const float firstStep = flushVmx(delta.lane[lane] * firstCorrection);
                const float secondStep = flushVmx(delta.lane[lane] * secondCorrection);
                newFirst.lane[lane] = flushVmx(firstStep + flushVmx(first[i].lane[lane]));
                newSecond.lane[lane] = flushVmx(secondStep + flushVmx(second[i].lane[lane]));
            }
            points[record.firstParticle] = newFirst;
            points[record.secondParticle] = newSecond;
        }
    }
}

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

// @ 0x82338730
void clothCollideCapsule(const ClothCapsuleCollisionView* self, const ClothCapsuleBoundView* bound,
                         uint32_t group, const LvlTableVector* reduction,
                         const LvlTableVector* expansion, uint32_t mode) {
    const ClothParticleGroup& particles = self->groups[group & 0x1FFFFFFFu];
    if (particles.count == 0)
        return;

    const auto aligned = [](const LvlTableVector* value) {
        return reinterpret_cast<const LvlTableVector*>(reinterpret_cast<uintptr_t>(value) & ~uintptr_t(15));
    };
    const auto* boundBytes = reinterpret_cast<const uint8_t*>(bound);
    const auto loadBound = [&](uint32_t offset) {
        return *aligned(reinterpret_cast<const LvlTableVector*>(boundBytes + offset));
    };
    const LvlTableVector padding = *aligned(expansion);
    const LvlTableVector capsuleRadius = loadBound(0x70);
    const LvlTableVector center = loadBound(0x40);
    const LvlTableVector axisStart = loadBound(0x90);
    LvlTableVector axis = loadBound(0xB0);
    const LvlTableVector axisLength = loadBound(0x80);
    LvlTableVector radius, radiusSq, broadRadiusSq;
    for (int lane = 0; lane < 4; ++lane) {
        axis.lane[lane] = flushVmx(axis.lane[lane]);
        radius.lane[lane] = flushVmx(flushVmx(capsuleRadius.lane[lane]) + flushVmx(padding.lane[lane]));
        radiusSq.lane[lane] = flushVmx(radius.lane[lane] * radius.lane[lane]);
        const float broadRadius = flushVmx(flushVmx(bound->broadRadius) + flushVmx(padding.lane[lane]));
        broadRadiusSq.lane[lane] = flushVmx(broadRadius * broadRadius);
    }

    LvlTableVector* positions = self->positions;
    const LvlTableVector* previous = self->previousPositions;
    const int32_t firstMovable = self->firstMovableParticle;
    const uint32_t* indices = particles.indices;
    const uint32_t paddedCount = (static_cast<uint32_t>(particles.count) + 31) & ~31u;
    auto* candidates = static_cast<uint32_t*>(__builtin_alloca(paddedCount * sizeof(uint32_t)));
    const uint32_t candidateCount = lvlTable_7D28_2h(paddedCount, positions, indices, candidates,
                                                   broadRadiusSq, center);
    auto* deltas = static_cast<LvlTableVector*>(__builtin_alloca(candidateCount * sizeof(LvlTableVector)));
    auto* distances = static_cast<LvlTableVector*>(__builtin_alloca(candidateCount * sizeof(LvlTableVector)));
    auto* hits = static_cast<uint32_t*>(__builtin_alloca(candidateCount * sizeof(uint32_t)));
    uint32_t hitCount = 0;
    for (uint32_t candidate = 0; candidate < candidateCount; ++candidate) {
        const uint32_t index = candidates[candidate];
        // Only later occurrences of the group's FIRST index are skipped. This
        // is not a general duplicate filter, nor an unconditional pinned index.
        if (candidate > 0 && index == indices[0])
            continue;
        const LvlTableVector point = aligned(positions)[index & 0x0FFFFFFFu];
        LvlTableVector relative;
        for (int lane = 0; lane < 4; ++lane)
            relative.lane[lane] = flushVmx(flushVmx(point.lane[lane]) - flushVmx(axisStart.lane[lane]));
        const float projection = flushVmx(dot(axis, relative, 3));
        LvlTableVector delta;
        for (int lane = 0; lane < 4; ++lane) {
            const uint32_t mask = lbl_82619BE0[lane];
            const float maskedProjection = flushVmx(maskLane(projection, mask));
            const float upperTest = flushVmx(maskLane(projection, mask, lbl_82619BD0[lane]));
            const float lowerTest = flushVmx(maskLane(lbl_82606750[lane], mask, lbl_82619BD0[lane]));
            const float upper = flushVmx(maskLane(axisLength.lane[lane], mask));
            float clamped = upperTest > upper ? axisLength.lane[lane] : projection;
            if (lowerTest > maskedProjection)
                clamped = lbl_82606750[lane];
            const float product = flushVmx(flushVmx(axis.lane[lane]) * flushVmx(clamped));
            const float closest = flushVmx(product + flushVmx(axisStart.lane[lane]));
            delta.lane[lane] = flushVmx(flushVmx(point.lane[lane]) - closest);
        }
        const float distanceSq = flushVmx(dot(delta, delta, 3));
        bool inside = true;
        for (int lane = 0; lane < 4; ++lane)
            inside &= radiusSq.lane[lane] > distanceSq;
        // The original overwrites the next slot even when rejecting a point.
        hits[hitCount] = index;
        deltas[hitCount] = delta;
        distances[hitCount] = {{distanceSq, distanceSq, distanceSq, distanceSq}};
        hitCount += inside;
    }

    for (uint32_t hit = 0; hit < hitCount; ++hit) {
        const uint32_t index = hits[hit];
        if (static_cast<int32_t>(index) < firstMovable)
            continue;
        const float distanceSq = distances[hit].lane[0];
        // VMX estimates are approximated here; preserve each refinement and
        // rounding step, including the w lane's different one/half constants.
        const float estimate = flushVmx(static_cast<float>(1.0 / std::sqrt(static_cast<double>(distanceSq))));
        LvlTableVector length;
        for (int lane = 0; lane < 4; ++lane) {
            const float y = estimate == flushVmx(lbl_82619BF0[lane]) ? lbl_82606750[lane] : estimate;
            const float square = flushVmx(flushVmx(y) * flushVmx(y));
            const float halfY = flushVmx(flushVmx(lbl_825CB7D0[lane]) * flushVmx(y));
            const float error = flushVmx(-flushVmx(flushVmx(distanceSq * square)
                                                  - flushVmx(lbl_825CB7C0[lane])));
            const float inverseLength = flushVmx(flushVmx(error * halfY) + flushVmx(y));
            length.lane[lane] = flushVmx(distanceSq * inverseLength);
        }
        const float reciprocal = flushVmx(1.0f / length.lane[0]);
        const LvlTableVector shrink = *aligned(reduction);
        LvlTableVector direction, step;
        for (int lane = 0; lane < 4; ++lane) {
            const float error = flushVmx(-flushVmx(flushVmx(reciprocal * length.lane[0])
                                                  - flushVmx(lbl_825CB7C0[lane])));
            const float inverseLength = flushVmx(flushVmx(reciprocal * error) + reciprocal);
            direction.lane[lane] = flushVmx(deltas[hit].lane[lane] * inverseLength);
            const float excess = flushVmx(radius.lane[lane] - length.lane[lane]);
            const float penetration = flushVmx(excess - flushVmx(shrink.lane[lane]));
            const float zero = flushVmx(lbl_82606750[lane]);
            // vmaxfp propagates NaNs; std::max would silently select an operand.
            step.lane[lane] = penetration != penetration || zero != zero
                                  ? penetration + zero : (penetration > zero ? penetration : zero);
        }
        const uint32_t slot = index & 0x0FFFFFFFu;
        // r4 retains the unaligned base; the callee rounds it down itself.
        auto* position = reinterpret_cast<LvlTableVector*>(reinterpret_cast<uintptr_t>(positions) + slot * 16u);
        const LvlTableVector origin = aligned(previous)[slot];
        lvlTable_7008_2h(reinterpret_cast<const LvlTableMotionView*>(self), position, mode,
                         direction, step, origin);
    }
}

// @ 0x823D85B8
void lvlTable_85B8_2hr(const LvlTableConstraintView* self, uint32_t constraint,
                       LvlTableVector* positions, const LvlTableVector& anchor) {
    const auto aligned = [](const LvlTableVector* base) {
        return reinterpret_cast<const LvlTableVector*>(reinterpret_cast<uintptr_t>(base) & ~uintptr_t(15));
    };
    // slwi wraps in 32 bits; the particle lookup retains two more index bits
    // than the vector-array accesses do.
    const uint32_t particle = self->particleIndices[constraint & 0x3FFFFFFFu];
    const uint32_t slot = constraint & 0x0FFFFFFFu;
    auto* output = const_cast<LvlTableVector*>(aligned(positions)) + (particle & 0x0FFFFFFFu);
    const LvlTableVector original = *output;
    const LvlTableVector rest = aligned(self->restLength)[slot];
    const LvlTableVector base = aligned(self->responseBase)[slot];
    const LvlTableVector scale = aligned(self->responseScale)[slot];
    const LvlTableVector origin = anchor;

    LvlTableVector delta;
    for (int lane = 0; lane < 4; ++lane)
        delta.lane[lane] = flushVmx(flushVmx(original.lane[lane]) - flushVmx(origin.lane[lane]));
    const float distanceSq = flushVmx(dot(delta, delta, 3));
    // Approximate vrsqrtefp with one float rounding after reciprocal sqrt.
    const float estimate = flushVmx(static_cast<float>(1.0 / std::sqrt(static_cast<double>(distanceSq))));
    LvlTableVector residual;
    bool keepOriginal[4];
    for (int lane = 0; lane < 4; ++lane) {
        const float zero = lbl_82606750[lane];
        const float one = lbl_825CB7C0[lane];
        const float length = flushVmx(rest.lane[lane]);
        const float lengthSq = flushVmx(length * length);
        const float excess = flushVmx(distanceSq - lengthSq);
        const float threshold = maskLane(zero, lbl_82619BE0[lane], lbl_82619BD0[lane]);
        keepOriginal[lane] = flushVmx(threshold) > flushVmx(maskLane(excess, lbl_82619BE0[lane]));

        // Replace the infinite zero-length estimate before Newton refinement.
        const float y = estimate == lbl_82619BF0[lane] ? zero : estimate;
        const float square = flushVmx(y * y);
        const float halfY = flushVmx(lbl_825CB7D0[lane] * y);
        const float error = flushVmx(-flushVmx(flushVmx(distanceSq * square) - one));
        const float inverseLength = flushVmx(__builtin_fmaf(error, halfY, y));
        const float direction = flushVmx(delta.lane[lane] * inverseLength);
        const float target = flushVmx(__builtin_fmaf(direction, length, flushVmx(origin.lane[lane])));
        residual.lane[lane] = flushVmx(flushVmx(original.lane[lane]) - target);
    }

    // This second estimate has no zero-length sentinel replacement.
    const float correctionSq = flushVmx(dot(residual, residual, 3));
    const float inverseCorrection = flushVmx(static_cast<float>(1.0 / std::sqrt(static_cast<double>(correctionSq))));
    for (int lane = 0; lane < 4; ++lane) {
        const float one = lbl_825CB7C0[lane];
        const float response = flushVmx(__builtin_fmaf(inverseCorrection, flushVmx(scale.lane[lane]),
                                                       flushVmx(base.lane[lane])));
        const float limit = maskLane(one, lbl_82619BE0[lane], lbl_82619BD0[lane]);
        // Negative responses survive; unordered comparisons select one.
        const float weight = flushVmx(limit) > flushVmx(maskLane(response, lbl_82619BE0[lane]))
                                 ? response : one;
        const float product = flushVmx(residual.lane[lane] * weight);
        const float corrected = flushVmx(-flushVmx(product - flushVmx(original.lane[lane])));
        output->lane[lane] = keepOriginal[lane] ? original.lane[lane] : corrected;
    }
}
