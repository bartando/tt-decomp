// Flash 2D affine matrices: {a, b, c, d, tx, ty}, applied as x' = a*x + c*y + tx,
// y' = b*x + d*y + ty. Callers are swfTEXT/swfBUTTON drawing and the HUD.

namespace rage {

// out = child * parent. `out` may alias either input: the original stores each
// result before loading the next row's inputs, so the order below is load-bearing.
// @ 0x823FA1E0
void swfConcatMatrix(float* out, const float* child, const float* parent) {
    out[0] = __builtin_fmaf(child[0], parent[0], parent[2] * child[1]);
    out[1] = __builtin_fmaf(parent[3], child[1], parent[1] * child[0]);
    out[2] = __builtin_fmaf(child[3], parent[2], child[2] * parent[0]);
    out[3] = __builtin_fmaf(parent[3], child[3], parent[1] * child[2]);
    out[4] = __builtin_fmaf(child[5], parent[2], child[4] * parent[0]) + parent[4];
    out[5] = __builtin_fmaf(parent[3], child[5], parent[1] * child[4]) + parent[5];
}

} // namespace rage
