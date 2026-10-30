// 4x4 matrices as four 16-byte rows (row 3 is translation).

namespace rage {

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

} // namespace rage
