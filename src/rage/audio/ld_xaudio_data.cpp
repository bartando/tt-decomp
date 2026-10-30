// SDK render dispatch table. The image contains PPC code addresses; the host
// port leaves them null until the corresponding kernels are bound.
struct XmaRenderStream;
using XmaRenderKernel = void (*)(XmaRenderStream*);

// @ 0x82006AF8 (.rdata) — [6][4][5], indexed by mode, format, channel slot.
extern "C" const XmaRenderKernel g_xaudioRenderKernels[120] = {};
