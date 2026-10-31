#include "rage/mat44.hpp"
#include <cstdint>
#include <cstring>

extern "C" const uint32_t g_affineXYZMask[4]; // @ 0x82619BE0 — xyz mask
extern "C" const uint32_t g_affineHomogeneousW[4]; // @ 0x82619BD0 — homogeneous w

// 4x4 matrices as four 16-byte rows (row 3 is translation).

namespace rage {

namespace {
float flushComposeVmx(float value) {
    uint32_t bits;
    std::memcpy(&bits, &value, 4);
    if ((bits & 0x7F800000u) == 0) {
        bits &= 0x80000000u;
        std::memcpy(&value, &bits, 4);
    }
    return value;
}
}

// @ 0x820C3AD8 | size: 0xF0 (was LocomotionStateAnim_3AD8_g)
// .text.s mislabels VMX128 loads and dot products as vmaddfp128/stvx128.
// Keep the early translation store: overlapping source matrices see it.
void mat44ComposeAffineInPlace(void* matrix, const void* transform) {
    auto* out = reinterpret_cast<float*>(reinterpret_cast<uintptr_t>(matrix) & ~uintptr_t(15));
    auto* source = reinterpret_cast<const float*>(reinterpret_cast<uintptr_t>(transform) & ~uintptr_t(15));
    float rows[4][4], right[4][4], result[4][4];
    std::memcpy(rows[0], out, 16);
    uint32_t translation[4];
    std::memcpy(translation, out + 12, 16);
    for (unsigned lane = 0; lane < 4; ++lane)
        translation[lane] = (translation[lane] & g_affineXYZMask[lane]) | g_affineHomogeneousW[lane];
    std::memcpy(out + 12, translation, 16);
    std::memcpy(right, source, 64);
    std::memcpy(rows[1], out + 4, 16);
    std::memcpy(rows[3], out + 12, 16);
    std::memcpy(rows[2], out + 8, 16);
    for (unsigned row = 0; row < 4; ++row) {
        for (unsigned col = 0; col < 3; ++col) {
            // vmsum3/4 accumulate products before rounding once to float.
            double sum = 0.0;
            for (unsigned k = 0; k < (row == 3 ? 4u : 3u); ++k)
                sum += static_cast<double>(flushComposeVmx(rows[row][k])) * flushComposeVmx(right[k][col]);
            result[row][col] = flushComposeVmx(static_cast<float>(sum));
        }
        // These merges copy raw bits, including denormals and NaN payloads.
        std::memcpy(&result[row][3], &rows[row][0], 4);
    }
    std::memcpy(out, result[0], 16);
    std::memcpy(out + 4, result[1], 16);
    std::memcpy(out + 12, result[3], 16);
    std::memcpy(out + 8, result[2], 16);
}

// A 3x3 minor, with the original single-precision product/FMA ordering.
// The translation cofactor starts its positive sum with b*f*g instead.
static float mat44Minor(float a, float b, float c, float d, float e, float f,
                        float g, float h, float i, bool translation) {
    const float cd = c * d, bf = b * f, ae = a * e;
    const float af = a * f, bd = b * d, ce = c * e;
    float sum;
    if (translation) {
        sum = bf * g;
        sum = __builtin_fmaf(ae, i, sum);
        sum = __builtin_fmaf(cd, h, sum);
    } else {
        sum = cd * h;
        sum = __builtin_fmaf(bf, g, sum);
        sum = __builtin_fmaf(ae, i, sum);
    }
    sum = -__builtin_fmaf(af, h, -sum);
    sum = -__builtin_fmaf(bd, i, -sum);
    return -__builtin_fmaf(ce, g, -sum);
}

// Expand along row zero, preserving the PPC minor accumulation and FMA order.
// @ 0x8223F008 | size: 0x134
float mat44Determinant(const float* m) {
    const float c0 = mat44Minor(m[5], m[6], m[7], m[9], m[10], m[11], m[13], m[14], m[15], false);
    const float c1 = mat44Minor(m[4], m[6], m[7], m[8], m[10], m[11], m[12], m[14], m[15], false);
    const float c2 = mat44Minor(m[4], m[5], m[7], m[8], m[9], m[11], m[12], m[13], m[15], false);
    const float c3 = mat44Minor(m[4], m[5], m[6], m[8], m[9], m[10], m[12], m[13], m[14], false);
    const float first = __builtin_fmaf(m[0], c0, -(m[1] * c1));
    const float third = __builtin_fmaf(m[2], c2, first);
    return -__builtin_fmaf(m[3], c3, -third);
}

// General 4x4 inverse: transpose the signed minors, scaled by 1/determinant.
// Unlike mat44InverseAffine this writes all 16 lanes and has no singularity
// check. Preserve column-at-a-time stores and reload each minor: overlapping
// buffers observe earlier writes (this is not an in-place-safe inverse).
// mat44Inverse (was phBoundCapsule_F140_g) @ 0x8223F140 | size: 0x614
void mat44Inverse(float* out, const float* m) {
    const float invDet = 1.0f / mat44Determinant(m);
    for (unsigned row = 0; row < 4; ++row) {
        unsigned rows[3];
        for (unsigned r = 0, n = 0; r < 4; ++r)
            if (r != row) rows[n++] = r * 4;
        for (unsigned col = 0; col < 4; ++col) {
            unsigned cols[3];
            for (unsigned c = 0, n = 0; c < 4; ++c)
                if (c != col) cols[n++] = c;
            const float minor = mat44Minor(
                m[rows[0] + cols[0]], m[rows[0] + cols[1]], m[rows[0] + cols[2]],
                m[rows[1] + cols[0]], m[rows[1] + cols[1]], m[rows[1] + cols[2]],
                m[rows[2] + cols[0]], m[rows[2] + cols[1]], m[rows[2] + cols[2]],
                row == 0 && col == 3);
            const float scaled = minor * invDet;
            out[col * 4 + row] = ((row + col) & 1) ? -scaled : scaled;
        }
    }
}

// Invert the affine xyz basis and translation; leave all four w lanes untouched.
// Reject |det| <= max(|basis element|) * 3.6e-7 without writing the destination.
// This is not the in-place wrapper at 0x820D7B30: keep the original load/store
// order, including when the buffers overlap. Products round before each FMA.
// mat44InverseAffine @ 0x820D7B90 | size: 0x24C
bool mat44InverseAffine(float* out, const float* m) {
    const float c00 = __builtin_fmaf(m[5], m[10], -(m[6] * m[9]));
    const float c01 = __builtin_fmaf(m[4], m[10], -(m[8] * m[6]));
    const float c02 = __builtin_fmaf(m[4], m[9], -(m[8] * m[5]));
    const float det = __builtin_fmaf(m[2], c02,
                      __builtin_fmaf(m[0], c00, -(m[1] * c01)));
    const auto selectMax = [](float a, float b) { return a >= b ? a : b; };
    const float max0 = selectMax(selectMax(__builtin_fabsf(m[0]),
                       __builtin_fabsf(m[1])), __builtin_fabsf(m[2]));
    const float max1 = selectMax(selectMax(__builtin_fabsf(m[4]),
                       __builtin_fabsf(m[5])), __builtin_fabsf(m[6]));
    const float max2 = selectMax(selectMax(__builtin_fabsf(m[8]),
                       __builtin_fabsf(m[9])), __builtin_fabsf(m[10]));
    const float max01 = max0 >= max1 ? max0 : max1;
    const float maxBasis = max01 >= max2 ? max01 : max2;
    if (__builtin_fabsf(det) <= maxBasis * 3.6e-7f)
        return false;

    const float invDet = 1.0f / det;
    const float x0 = invDet * c00;
    const float x1 = -(invDet * c01);
    const float x2 = invDet * c02;
    out[0] = x0;
    out[8] = x2;
    out[4] = x1;
    out[12] = -__builtin_fmaf(m[14], x2,
               __builtin_fmaf(x1, m[13], x0 * m[12]));

    const float c10 = __builtin_fmaf(m[1], m[10], -(m[9] * m[2]));
    const float c12 = __builtin_fmaf(m[9], m[0], -(m[1] * m[8]));
    const float c11 = __builtin_fmaf(m[10], m[0], -(m[2] * m[8]));
    const float y1 = invDet * c11;
    const float y0 = -(c10 * invDet);
    const float y2 = -(invDet * c12);
    out[5] = y1;
    out[1] = y0;
    out[9] = y2;
    out[13] = -__builtin_fmaf(m[14], y2,
               __builtin_fmaf(y1, m[13], m[12] * y0));

    const float c20 = __builtin_fmaf(m[6], m[1], -(m[5] * m[2]));
    const float c21 = __builtin_fmaf(m[6], m[0], -(m[4] * m[2]));
    const float c22 = __builtin_fmaf(m[5], m[0], -(m[4] * m[1]));
    const float z0 = c20 * invDet;
    out[2] = z0;
    const float z1 = -(invDet * c21);
    const float z2 = invDet * c22;
    out[10] = z2;
    out[6] = z1;
    out[14] = -__builtin_fmaf(m[14], z2,
               __builtin_fmaf(z1, m[13], m[12] * z0));
    return true;
}

// Snapshot all four rows before inversion so the source is safe from writes.
// Failed inversions preserve the matrix, and successful ones preserve w lanes.
// mat44InverseAffineInPlace (was LocomotionStateAnim_7B30_g) @ 0x820D7B30 | size: 0x60
bool mat44InverseAffineInPlace(float* matrix) {
    alignas(16) float snapshot[16];
    for (unsigned i = 0; i < 16; ++i)
        snapshot[i] = matrix[i];
    return mat44InverseAffine(matrix, snapshot);
}

// out = point * matrix. Lane 0 accumulates z, w, y, x; lanes 1-3 w, x, z, y, all
// fused. Each lane is stored before the next one's loads, so `out` may alias `point`.
// @ 0x8214EA10
void mat44TransformPoint(const float* matrix, const float* point, float* out) {
    const float* m = matrix;
    out[0] = __builtin_fmaf(point[0], m[0], __builtin_fmaf(m[4], point[1],
             __builtin_fmaf(m[12], point[3], m[8] * point[2])));
    for (unsigned c = 1; c < 4; ++c) {
        out[c] = __builtin_fmaf(m[4 + c], point[1], __builtin_fmaf(m[8 + c], point[2],
                 __builtin_fmaf(m[c], point[0], m[12 + c] * point[3])));
    }
}

// out = point * matrix. Stores happen between lanes, so overlapping buffers
// affect later loads. Each lane starts with y, then accumulates w and x/z.
// mat44TransformVector @ 0x8223ECB0 | size: 0xD4
void mat44TransformVector(float* out, const float* point, const float* m) {
    out[0] = __builtin_fmaf(point[0], m[0], __builtin_fmaf(m[8], point[2],
             __builtin_fmaf(m[12], point[3], m[4] * point[1])));
    for (unsigned c = 1; c < 4; ++c) {
        out[c] = __builtin_fmaf(m[8 + c], point[2], __builtin_fmaf(m[c], point[0],
                 __builtin_fmaf(m[12 + c], point[3], m[4 + c] * point[1])));
    }
}

} // namespace rage
