#include "platform/audio.hpp"

// This host build has no XMA hardware/codec backend. Capabilities and queued
// output are empty; operations that require decoding return E_NOTIMPL. In
// particular, no input is accepted and no decoded frames/samples are invented.
namespace { int32_t xmaBackendNotSupported() { return HostMediaNotSupported; } }
int32_t XmaDecoder_IsEnabled(void*) { return 0; }
int32_t XmaDecoder_Lock(void*) { return xmaBackendNotSupported(); }
int32_t XmaDecoder_Unlock(void*) { return xmaBackendNotSupported(); }
void XmaDecoder_Wait(void*) {} // No work can be submitted to this backend.
uint32_t XmaDecoder_Available(void*, uint32_t) { return 0; }
uint32_t XmaDecoder_Peek(void*, uint32_t, const void** input) { if (input) *input = nullptr; return 0; }
void XmaDecoder_Consume(void*, uint32_t, uint32_t, const void** input) { if (input) *input = nullptr; }
uint32_t XmaDecoder_SamplesPlayed(void*, uint32_t) { return 0; }
int32_t XmaDecoder_HasInputSpace(void*, uint32_t) { return 0; }
int32_t XmaDecoder_IsBufferPending(void*, uint32_t, const void*) { return 0; }
uint32_t XmaDecoder_GetStreamStatus(void*, uint32_t) { return static_cast<uint32_t>(xmaBackendNotSupported()); }
int32_t XmaDecoder_IsInputEmpty(void*, uint32_t) { return 1; }
int32_t XmaDecoder_SubmitData(void*, uint32_t, const void*, uint32_t) { return xmaBackendNotSupported(); }
int32_t XmaDecoder_SetReadPosition(void*, uint32_t, uint32_t, uint32_t) { return xmaBackendNotSupported(); }
int32_t XmaDecoder_SetLoopRegion(void*, uint32_t, const XmaLoopRegion*) { return xmaBackendNotSupported(); }

// Hardware MMIO has no host mapping. Native lock completion rejects the
// unsupported backend before observing this register. PPC checks supply it.
volatile uint32_t g_xmaCurrentContextRegister = UINT32_MAX; // @ 0x7FEA1818
