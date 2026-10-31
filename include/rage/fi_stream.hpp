#pragma once

#include <stdint.h>

#ifdef __cplusplus
#include "rage/ptr32.hpp"
#include <cstddef>

namespace rage {
// The stream holds a device, not its own vtable. No virtual destructor: these
// are the leading device slots used by the original stream implementation.
class fiStreamDevice {
public:
    virtual void Slot0() = 0;
    virtual int32_t Open(const char* path, uint32_t flags) = 0;
    virtual void Slot2() = 0;
    virtual int32_t Read(uint32_t handle, void* destination, int32_t bytes) = 0;
    virtual int32_t Write(uint32_t handle, const void* source, int32_t bytes) = 0;
    virtual int32_t Seek(uint32_t handle, uint32_t position, int32_t origin) = 0;
    virtual int32_t Close(uint32_t handle) = 0;
    virtual void Slot7() = 0;
    virtual int32_t Flush(uint32_t handle) = 0;
};

struct fiStreamBuf {
    ptr32<fiStreamDevice> device; // +00
    uint32_t handle;             // +04
    ptr32<uint8_t> buffer;       // +08
    uint32_t position;          // +0C absolute buffer origin
    int32_t cursor;             // +10
    int32_t end;                // +14 zero in write mode
    int32_t capacity;           // +18
};
static_assert(sizeof(fiStreamBuf) == 0x1C);
static_assert(offsetof(fiStreamBuf, capacity) == 0x18);
}
extern "C" {
#endif

// @ 0x822E3040 — searches asset roots for the first successful open. r6 unused.
void* fiStreamBuf_OpenAll(void* assets, const char* name, const char* extension,
                          uint32_t unused, uint32_t flags);
// @ 0x822E3518
void* fiStream_Open(const char* path, int32_t flags);
// @ 0x822E3828 — returns bytes transferred, or -1.
int32_t fiStreamBuf_Read(void* stream, void* destination, int32_t bytes);
// @ 0x822E3CD8 — reads little-endian 32-bit words into native integers. Returns
// complete words, leaving any trailing incomplete word as raw bytes.
int32_t fiStreamBuf_ReadWords(void* stream, void* destination, int32_t words);
// @ 0x822E3BA8 — reconciles the device position, empties the window, then Flush.
int32_t fiStreamBuf_Finalize(void* stream);
// @ 0x822E3AC8 — Finalize followed by an absolute Seek.
int32_t fiStreamBuf_Reset(void* stream, int32_t position);
// @ 0x822E3B38 — closes the handle and returns the stream slot to its pool.
int32_t fiStreamBuf_Close(void* stream);

#ifdef __cplusplus
}
#endif
