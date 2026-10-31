#include "grc/image_state.hpp"
#include "fx_effects.hpp"
#include <cstddef>

extern const float* g_fxBillboardUVs;              // @ 0x825C2B10
extern float g_fxBillboardRight[4];               // @ 0x82715FC0
extern float g_fxBillboardUp[4];                  // @ 0x82715FB0
extern float g_fxBillboardRotatedAxes[4096];       // @ 0x82715FD0 (512 pairs, eight floats each)

namespace {
struct FxBillboardVertex {
    float position[3];
    float normal[3];
    uint32_t color;
    float uv[2];
};
static_assert(sizeof(FxBillboardVertex) == 36);
static_assert(offsetof(FxBillboardVertex, color) == 24);
static_assert(offsetof(FxBillboardVertex, uv) == 28);
}

// Appends a camera-facing textured quad to the shared immediate vertex stream (716 bytes).
// Xenon: r3 = UV index, f1..f6 = angle/centre/half extents, r10 = packed colour.
// The camera setup at 0x8240FE58 builds the axes and 512 rotated axis pairs.
// A nonzero count-only flag permits a null cursor; the vertex count still grows.
// @ 0x82410058
void fxDrawBillboardQuad(uint32_t uvIndex, float angle, float x, float y, float z,
                         float halfWidth, float halfHeight, uint32_t color) {
    const float* right = g_fxBillboardRight;
    const float* up = g_fxBillboardUp;
    if (angle != 0.0f) {
        // Two separately rounded fmuls, then fctiwz and a nine-bit wrap.
        float turns = angle * 0.15915493667125702f;
        float scaled = turns * 512.0f;
        int32_t phase;
        if (scaled >= 2147483648.0f) {
            phase = 2147483647;
        } else if (!(scaled > -2147483648.0f)) {
            phase = (-2147483647 - 1); // fctiwz: negative overflow and NaN
        } else {
            phase = static_cast<int32_t>(scaled);
        }
        right = g_fxBillboardRotatedAxes + (static_cast<uint32_t>(phase) & 511) * 8;
        up = right + 4;
    }

    const float center[3] = {x, y, z};
    float corners[4][3];
    for (unsigned axis = 0; axis < 3; ++axis) {
        float r = right[axis] * halfWidth;
        float u = up[axis] * halfHeight;
        // Preserve fadds/fsubs order, including the third corner's (u+r)+centre.
        float minusRight = center[axis] - r;
        corners[0][axis] = minusRight - u;
        corners[1][axis] = (r + center[axis]) - u;
        corners[2][axis] = (u + r) + center[axis];
        corners[3][axis] = minusRight + u;
    }

    const float* uv = g_fxBillboardUVs + ((uvIndex << 4) >> 2);
    const uint32_t countOnly = g_fxCountOnly;
    for (unsigned corner = 0; corner < 4; ++corner) {
        if (countOnly == 0 || g_fxVertexCursor != 0) {
            auto* vertex = reinterpret_cast<FxBillboardVertex*>(static_cast<uintptr_t>(g_fxVertexCursor));
            g_fxVertexCursor += sizeof(FxBillboardVertex);
            for (unsigned axis = 0; axis < 3; ++axis) {
                vertex->position[axis] = corners[corner][axis];
                vertex->normal[axis] = 0.0f;
            }
            vertex->color = color;
            vertex->uv[0] = uv[corner == 1 || corner == 2 ? 2 : 0];
            vertex->uv[1] = uv[corner < 2 ? 1 : 3];
        }
    }
    g_fxVertexCount += 4;
}
extern const float g_fxVertexDepth; // @ 0x8202D110

// Append a 2D vertex using the current normal, colour and UV state.
// @ 0x82406010
void fxEmitVertex2D(float x, float y) {
    if (g_fxCountOnly == 0 || g_fxVertexCursor != 0) {
        auto* vertex = reinterpret_cast<FxBillboardVertex*>(static_cast<uintptr_t>(g_fxVertexCursor));
        g_fxVertexCursor += sizeof(FxBillboardVertex);
        vertex->position[0] = x;
        vertex->position[1] = y;
        vertex->position[2] = g_fxVertexDepth;
        vertex->normal[0] = g_fxVertexNormalX;
        vertex->normal[1] = g_fxVertexNormalY;
        vertex->normal[2] = g_fxVertexNormalZ;
        vertex->color = g_fxCurrentColor;
        vertex->uv[0] = g_fxVertexU;
        vertex->uv[1] = g_fxVertexV;
    }
    ++g_fxVertexCount;
}
