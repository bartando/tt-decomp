// 4x4 matrices as four 16-byte rows (row 3 is translation).

namespace rage {

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
