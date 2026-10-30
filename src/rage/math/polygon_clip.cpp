#include "rage/polygon_clip.hpp"
#include "../../game/camera/pong_camera.hpp"

// The VMX interpolation rounds its multiply before adding the previous vertex.
#if defined(__clang__)
#pragma clang fp contract(off)
#elif defined(__GNUC__)
#pragma GCC optimize("fp-contract=off")
#endif

extern "C" const float lbl_8202D110; // @ 0x8202D110
extern "C" {
extern const uint32_t lbl_82619BE0[4]; // @ 0x82619BE0 — xyz mask
extern const uint32_t lbl_82619BD0[4]; // @ 0x82619BD0 — homogeneous w = 1
extern const float lbl_82606740[4];    // @ 0x82606740 — zero vector
extern const float lbl_82606750[4];    // @ 0x82606750 — normalization zero
extern const float lbl_82619BF0[4];    // @ 0x82619BF0 — positive infinity
extern const float lbl_825CB7C0[4];    // @ 0x825CB7C0 — (1, 1, 1, 0)
extern const float lbl_825CB7D0[4];    // @ 0x825CB7D0 — (0.5, 0.5, 0.5, 0)
extern const float lbl_825CA420[4];    // @ 0x825CA420 — (0.1, 0.1, 0.1, 0)
extern const float lbl_825C8078;       // @ 0x825C8078 — 0.01
extern const float lbl_825C5938;       // @ 0x825C5938 — -1
extern const float lbl_8202D184;       // @ 0x8202D184 — 2
extern const uint32_t g_boxFaceIndices[24]; // @ 0x825D4A90
}

namespace rage {

// These names describe the actual helpers, rather than their capsule/animation auto-names.
extern bool mat44InverseAffineInPlace(float* matrix); // @ 0x820D7B30
extern void mergeAabbCenterSize(float (*destination)[4], const float* center,
                               const float* fullSize); // @ 0x82143F90
// LTCG leaves the output in r8, with unused integer slots r4..r7.
extern void buildClipFrustumPlanes(void* context, uint32_t, uint32_t, uint32_t, uint32_t,
                                   float (*planes)[4], float nearClip, float farClip,
                                   float fov, float aspect, float offset); // @ 0x821480C0

namespace {

float flushClipVmx(float value) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof(bits));
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        __builtin_memcpy(&value, &bits, sizeof(value));
    }
    return value;
}

float clipHomogeneousLane(float value, unsigned lane) {
    uint32_t bits;
    __builtin_memcpy(&bits, &value, sizeof(bits));
    bits = (bits & lbl_82619BE0[lane]) | lbl_82619BD0[lane];
    __builtin_memcpy(&value, &bits, sizeof(value));
    return value;
}

void transformClipPoint(float* point, const float (*matrix)[4]) {
    float homogeneous[4];
    for (unsigned lane = 0; lane < 4; ++lane)
        homogeneous[lane] = clipHomogeneousLane(point[lane], lane);
    for (unsigned axis = 0; axis < 3; ++axis) {
        // vmsum4fp128 accumulates all four products before rounding to float.
        double sum = 0.0;
        for (unsigned row = 0; row < 4; ++row)
            sum += static_cast<double>(flushClipVmx(homogeneous[row])) * flushClipVmx(matrix[row][axis]);
        point[axis] = flushClipVmx(static_cast<float>(sum));
    }
    // The original merge instructions put the input x, not homogeneous w, here.
    point[3] = homogeneous[0];
}

} // namespace

// Formerly phBoundCapsule_3F08_g / phBoundCapsule::ValidateAndSetExtents.
// Inferred identity: callers accumulate three projected scene boxes (0x821490A0)
// or six 48-byte boxes (0x821459C4). The callee unions center/full-size AABBs.
// @ 0x82143F08 | size: 0x84
void expandAabbByOffsetBox(float (*destination)[4], const float (*box)[4]) {
    bool empty = true;
    for (unsigned lane = 0; lane < 4; ++lane) {
        uint32_t bits;
        __builtin_memcpy(&bits, &box[1][lane], sizeof(bits));
        bits &= lbl_82619BE0[lane];
        float size;
        __builtin_memcpy(&size, &bits, sizeof(size));
        empty &= flushClipVmx(size) == 0.0f;
    }
    if (empty) return;

    alignas(16) float center[4];
    for (unsigned lane = 0; lane < 4; ++lane)
        center[lane] = flushClipVmx(flushClipVmx(box[0][lane]) + flushClipVmx(box[2][lane]));
    mergeAabbCenterSize(destination, center, box[1]);
}

// Eight corners of an AABB, in the order consumed by g_boxFaceIndices.
// Formerly phBoundCapsule_7EF8_g; r3=out, r4=center, r5=full size.
// @ 0x82147EF8
void buildBoxCorners(float (*out)[4], const float* center, const float* size) {
    float halfSize[3];
    for (unsigned lane = 0; lane < 3; ++lane)
        halfSize[lane] = flushClipVmx(flushClipVmx(size[lane]) * 0.5f);

    // The original loads size before broadcasting center, then edits xyz only.
    // Snapshot both inputs before any stores so output/input aliases work too.
    float origin[4];
    __builtin_memcpy(origin, center, sizeof(origin));
    for (unsigned corner = 0; corner < 8; ++corner)
        __builtin_memcpy(out[corner], origin, sizeof(origin));
    for (unsigned corner = 0; corner < 8; ++corner) {
        out[corner][0] += (corner & 1) ? halfSize[0] : -halfSize[0];
        out[corner][1] += (corner & 2) ? halfSize[1] : -halfSize[1];
        out[corner][2] += (corner & 4) ? -halfSize[2] : halfSize[2];
    }
}

// @ 0x82147A88
void clipPolygonToPlane(void* /*context*/, int32_t vertexCount, const float (*vertices)[4],
                        int32_t* outputCount, float (*output)[4], const float* plane) {
    // Misnamed SinglesNetworkClient_7A88_2hr in the generated symbol map.
    // Sutherland–Hodgman: retain the half-space dot(plane.xyz, vertex.xyz) + plane.w <= 0.
    // The caller at 0x82147D18 clips a polygon successively against six planes.
    *outputCount = 0;
    if (vertexCount <= 0) {
        return;
    }

    float previous[4];
    __builtin_memcpy(previous, vertices[vertexCount - 1], sizeof(previous));

    for (int32_t i = 0; i < vertexCount; ++i) {
        float current[4];
        __builtin_memcpy(current, vertices[i], sizeof(current));

        // The original uses different addition orders at the two endpoints:
        // previous = (nx*x + ny*y) + nz*z; current = nx*x + (ny*y + nz*z).
        float previousY = plane[1] * previous[1];
        float previousXY = __builtin_fmaf(plane[0], previous[0], previousY);
        float previousDot = __builtin_fmaf(plane[2], previous[2], previousXY);
        float previousDistance = previousDot + plane[3];
        float currentZ = plane[2] * current[2];
        float currentYZ = __builtin_fmaf(plane[1], current[1], currentZ);
        float currentDot = __builtin_fmaf(plane[0], current[0], currentYZ);
        float currentDistance = currentDot + plane[3];

        // Ordered <= also rejects NaNs, as fcmpu followed by bgt/bso does.
        bool currentInside = currentDistance <= 0.0f;
        bool previousInside = previousDistance <= 0.0f;
        if (currentInside != previousInside) {
            float fraction = previousDistance / (previousDistance - currentDistance);
            int32_t index = (*outputCount)++;
            for (int lane = 0; lane < 4; ++lane) {
                float delta = current[lane] - previous[lane];
                float scaled = delta * fraction;
                output[index][lane] = previous[lane] + scaled;
            }
        }
        if (currentInside) {
            __builtin_memcpy(output[(*outputCount)++], current, sizeof(current));
        }
        __builtin_memcpy(previous, current, sizeof(previous));
    }
}

// @ 0x82147BF8
void clipLineToPlane(void* /*context*/, int32_t vertexCount, const float (*vertices)[4],
                     int32_t* outputCount, float (*output)[4], const float* plane) {
    *outputCount = vertexCount;
    float firstZ = vertices[0][2] * plane[2];
    float firstYZ = __builtin_fmaf(vertices[0][1], plane[1], firstZ);
    float firstDistance = __builtin_fmaf(vertices[0][0], plane[0], firstYZ) + plane[3];
    float secondZ = vertices[1][2] * plane[2];
    float secondYZ = __builtin_fmaf(vertices[1][1], plane[1], secondZ);
    float secondDistance = __builtin_fmaf(plane[0], vertices[1][0], secondYZ) + plane[3];

    bool firstInside = firstDistance <= lbl_8202D110;
    bool secondInside = secondDistance <= lbl_8202D110;
    if (!firstInside && !secondInside) {
        *outputCount = 0;
        return;
    }
    if (firstInside && secondInside) {
        __builtin_memcpy(output, vertices, 2 * sizeof(*output));
        return;
    }
    float fraction = firstDistance / (firstDistance - secondDistance);
    for (int lane = 0; lane < 4; ++lane) {
        float delta = vertices[1][lane] - vertices[0][lane];
        float scaled = delta * fraction;
        float intersection = vertices[0][lane] + scaled;
        output[0][lane] = firstInside ? vertices[0][lane] : intersection;
        output[1][lane] = secondInside ? vertices[1][lane] : intersection;
    }
}

// @ 0x82147D18
void clipPolygonToFrustum(void* context, int32_t /*unusedCount*/, const float (*vertices)[4],
                          int32_t* outputCount, float (*output)[4], const float (*planes)[4],
                          const float* referencePoint) {
    alignas(16) float scratch[16][4];
    __builtin_memcpy(scratch, vertices, 4 * sizeof(scratch[0]));
    int32_t count = 4;
    for (int plane = 0; plane < 6; ++plane) {
        if (referencePoint) {
            // vmsum3fp128 rounds the dot product to float before subtracting plane.w.
            float dot = static_cast<float>(static_cast<double>(planes[plane][0]) * referencePoint[0] +
                                           static_cast<double>(planes[plane][1]) * referencePoint[1] +
                                           static_cast<double>(planes[plane][2]) * referencePoint[2]);
            if (dot - planes[plane][3] > 0.0f) {
                continue;
            }
        }
        clipPolygonToPlane(context, count, scratch, outputCount, output, planes[plane]);
        count = *outputCount;
        if (count == 0) {
            return;
        }
        if (count > 0) {
            __builtin_memcpy(scratch, output, static_cast<unsigned>(count) * sizeof(scratch[0]));
        }
    }
}

// @ 0x82147E18
void clipLineToFrustum(void* context, int32_t /*unusedCount*/, const float (*vertices)[4],
                       int32_t* outputCount, float (*output)[4], const float (*planes)[4],
                       const float* referencePoint) {
    alignas(16) float scratch[2][4];
    __builtin_memcpy(scratch, vertices, sizeof(scratch));
    int32_t count = 2;
    for (int plane = 0; plane < 6; ++plane) {
        if (referencePoint) {
            float dot = static_cast<float>(static_cast<double>(planes[plane][0]) * referencePoint[0] +
                                           static_cast<double>(planes[plane][1]) * referencePoint[1] +
                                           static_cast<double>(planes[plane][2]) * referencePoint[2]);
            if (dot - planes[plane][3] > lbl_8202D110)
                continue;
        }
        clipLineToPlane(context, count, scratch, outputCount, output, planes[plane]);
        count = *outputCount;
        if (count == 0)
            return;
        if (count > 0)
            __builtin_memcpy(scratch, output, static_cast<unsigned>(count) * sizeof(scratch[0]));
    }
}

// clipAabbToFrustum @ 0x821481D8 | size: 0x42C
// Inferred name: called by the active-camera wrapper at 0x82148608 and the camera
// fitting path at 0x82148CD8. The generated name phBoundCapsule_81D8_g is misleading.
bool clipAabbToFrustum(void* context, float (*box)[4], const float (*cameraToWorld)[4],
                       uint32_t /*r6*/, uint32_t /*r7*/, uint32_t /*r8*/, uint32_t /*r9*/,
                       const float* referencePoint, float nearClip, float farClip, float fov, float aspect) {
    bool empty = true;
    for (unsigned lane = 0; lane < 4; ++lane) {
        uint32_t bits;
        __builtin_memcpy(&bits, &box[1][lane], sizeof(bits));
        bits &= lbl_82619BE0[lane];
        float extent;
        __builtin_memcpy(&extent, &bits, sizeof(extent));
        empty &= flushClipVmx(extent) == 0.0f;
    }
    if (empty)
        return false; // Unlike rejection below, an empty input is left untouched.

    alignas(16) float corners[8][4];
    buildBoxCorners(corners, box[0], box[1]);
    alignas(16) float worldToCamera[4][4];
    __builtin_memcpy(worldToCamera, cameraToWorld, sizeof(worldToCamera));
    mat44InverseAffineInPlace(&worldToCamera[0][0]);
    for (unsigned corner = 0; corner < 8; ++corner)
        transformClipPoint(corners[corner], worldToCamera);

    alignas(16) float planes[6][4];
    // fsel chooses the 0.1 default for unordered input as well as values above 0.1.
    const float selectedNear = 0.1f - nearClip >= 0.0f ? nearClip : 0.1f;
    buildClipFrustumPlanes(context, 0, 0, 0, 0, planes, selectedNear, farClip, fov, aspect, 0.0f);
    float minimum[3] = {__FLT_MAX__, __FLT_MAX__, __FLT_MAX__};
    float maximum[3] = {-__FLT_MAX__, -__FLT_MAX__, -__FLT_MAX__};
    int32_t totalCount = 0;
    for (unsigned face = 0; face < 6; ++face) {
        alignas(16) float quad[4][4];
        for (unsigned vertex = 0; vertex < 4; ++vertex)
            __builtin_memcpy(quad[vertex], corners[g_boxFaceIndices[face * 4 + vertex]], sizeof(quad[vertex]));
        int32_t count = 0;
        alignas(16) float clipped[16][4];
        clipPolygonToFrustum(context, 4, quad, &count, clipped, planes, referencePoint);
        totalCount += count;
        for (int32_t vertex = 0; vertex < count; ++vertex) {
            transformClipPoint(clipped[vertex], cameraToWorld);
            for (unsigned axis = 0; axis < 3; ++axis) {
                const float value = clipped[vertex][axis];
                // fcmpu + blt/bgt updates on equality and unordered comparisons.
                if (!(minimum[axis] < value)) minimum[axis] = value;
                if (!(maximum[axis] > value)) maximum[axis] = value;
            }
        }
    }
    if (totalCount == 0) {
        for (unsigned vector = 0; vector < 3; ++vector)
            __builtin_memcpy(box[vector], lbl_82606740, sizeof(box[vector]));
        return false;
    }
    for (unsigned axis = 0; axis < 3; ++axis) {
        const float lo = flushClipVmx(minimum[axis]);
        const float hi = flushClipVmx(maximum[axis]);
        box[1][axis] = flushClipVmx(hi - lo);
        const float sum = flushClipVmx(lo + hi);
        box[0][axis] = flushClipVmx(sum * 0.5f);
    }
    // The original writes indeterminate stack words to center.w/size.w on success.
    // Preserve those padding lanes; the auxiliary vector is untouched on success.
    return true;
}

// clipAabbToActiveCamera (was phBoundCapsule_8608_g) @ 0x82148608 | size: 0x9C
// Cache the frame camera before the aspect call, then reload its clip fields.
bool clipAabbToActiveCamera(void* context, float (*box)[4], const float* referencePoint) {
    const auto* owner = *reinterpret_cast<const uint8_t* const*>(0x8260641Cu);
    const auto* cameras = *reinterpret_cast<const uint8_t* const*>(owner + 24);
    const uint32_t frame = *reinterpret_cast<const uint32_t*>(0x825C4898u);
    const auto* camera = cameras + frame * 912;
    const float aspect = reinterpret_cast<const grcViewport*>(camera)->GetAspectRatio();
    const float nearClip = *reinterpret_cast<const float*>(camera + 832);
    const float cap = *reinterpret_cast<const float*>(0x8202CFE8u);
    const double fallback = *reinterpret_cast<const double*>(0x82079FB8u);
    const float selectedNear = cap - nearClip >= 0.0f ? nearClip : static_cast<float>(fallback);
    return clipAabbToFrustum(context, box, reinterpret_cast<const float (*)[4]>(camera + 64),
                             0, 0, 0, 0, referencePoint, selectedNear,
                             *reinterpret_cast<const float*>(camera + 836),
                             *reinterpret_cast<const float*>(camera + 824), aspect);
}

// projectAabbToHorizontalPlane @ 0x821493F8 | size: 0x350
// Inferred name: the caller at 0x821490A0 projects three scene bounds onto two
// horizontal planes. The generated name phBoundCapsule_93F8_g is misleading.
void projectAabbToHorizontalPlane(void* context, const float (*box)[4], const float (*camera)[4],
                                   float (*output)[4], const float* limits) {
    bool empty = true;
    for (unsigned lane = 0; lane < 4; ++lane) {
        uint32_t bits;
        __builtin_memcpy(&bits, &box[1][lane], sizeof(bits));
        bits &= lbl_82619BE0[lane];
        float extent;
        __builtin_memcpy(&extent, &bits, sizeof(extent));
        empty &= flushClipVmx(extent) == 0.0f;
    }
    if (!empty) {
        alignas(16) float center[4];
        for (unsigned lane = 0; lane < 4; ++lane)
            center[lane] = flushClipVmx(flushClipVmx(box[0][lane]) + flushClipVmx(box[2][lane]));
        alignas(16) float corners[8][4];
        buildBoxCorners(corners, center, box[1]);

        const float planeY = limits[1];
        const float height = camera[4][1] - planeY;
        float minimum[3] = {__FLT_MAX__, __FLT_MAX__, __FLT_MAX__};
        float maximum[3] = {-__FLT_MAX__, -__FLT_MAX__, -__FLT_MAX__};
        for (unsigned corner = 0; corner < 8; ++corner) {
            float direction[3];
            double lengthSum = 0.0;
            for (unsigned axis = 0; axis < 3; ++axis) {
                direction[axis] = flushClipVmx(flushClipVmx(corners[corner][axis]) -
                                               flushClipVmx(camera[4][axis]));
                lengthSum += static_cast<double>(direction[axis]) * direction[axis];
            }
            const float lengthSquared = flushClipVmx(static_cast<float>(lengthSum));
            // Preserve the VMX reciprocal-square-root refinement and its separate
            // rounding steps; cancelling normalization changes projected bounds.
            float inverseLength = flushClipVmx(static_cast<float>(
                1.0 / __builtin_sqrt(static_cast<double>(lengthSquared))));
            if (inverseLength == lbl_82619BF0[0]) inverseLength = lbl_82606750[0];
            const float inverseSquared = flushClipVmx(inverseLength * inverseLength);
            const float halfInverse = flushClipVmx(lbl_825CB7D0[0] * inverseLength);
            const float residual = -flushClipVmx(
                flushClipVmx(lengthSquared * inverseSquared) - lbl_825CB7C0[0]);
            inverseLength = flushClipVmx(flushClipVmx(residual * halfInverse) + inverseLength);
            for (unsigned axis = 0; axis < 3; ++axis)
                direction[axis] = flushClipVmx(direction[axis] * inverseLength);

            const float reciprocalY = lbl_825C5938 / direction[1];
            const float distance = reciprocalY * height;
            for (unsigned axis = 0; axis < 3; ++axis) {
                const float scaled = flushClipVmx(direction[axis] * flushClipVmx(distance));
                const float projected = axis == 1 ? planeY :
                    flushClipVmx(scaled + flushClipVmx(camera[4][axis]));
                // blt/bgt skip updates only on ordered strict comparisons.
                if (!(minimum[axis] < projected)) minimum[axis] = projected;
                if (!(maximum[axis] > projected)) maximum[axis] = projected;
            }
        }
        for (unsigned axis = 0; axis < 3; axis += 2) {
            const float highDelta = maximum[axis] - limits[axis];
            maximum[axis] = highDelta >= 0.0f ? limits[axis] : maximum[axis];
            const float lowLimit = -limits[axis];
            const float lowDelta = minimum[axis] - lowLimit;
            minimum[axis] = lowDelta >= 0.0f ? minimum[axis] : lowLimit;
        }
        if (!(maximum[0] <= minimum[0]) && !(maximum[2] <= minimum[2])) {
            const float* padding = planeY < lbl_825C8078 ? lbl_825CA420 : lbl_82606740;
            // VMX computes size before center; w comes from uninitialized stack
            // words in the original. Preserve the two output padding lanes here.
            for (unsigned axis = 0; axis < 3; ++axis) {
                const float hi = flushClipVmx(maximum[axis]);
                const float lo = flushClipVmx(minimum[axis]);
                const float difference = flushClipVmx(hi - lo);
                output[1][axis] = flushClipVmx(difference + flushClipVmx(padding[axis]));
                const float sum = flushClipVmx(hi + lo);
                output[0][axis] = flushClipVmx(sum * (1.0f / lbl_8202D184));
            }
            clipAabbToActiveCamera(context, output, nullptr);
            return;
        }
    }
    for (unsigned vector = 0; vector < 3; ++vector)
        __builtin_memcpy(output[vector], lbl_82606740, sizeof(output[vector]));
}

} // namespace rage
