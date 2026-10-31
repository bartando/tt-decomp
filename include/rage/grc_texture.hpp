#pragma once
#include <cstdint>

namespace rage {
// grcTextureXenon virtual interface, vtable @ 0x820353CC.
struct grcTexture {
    virtual void destructor(bool deleteThis);       // slot  0
    virtual void vfn_1();                           // slot  1
    virtual void vfn_2();                           // slot  2
    virtual void vfn_3();                           // slot  3
    virtual void vfn_4();                           // slot  4
    virtual void vfn_5();                           // slot  5
    virtual void vfn_6();                           // slot  6
    virtual void ApplyState(void* param);           // slot  7
    virtual int32_t GetWidth();                   // slot  8
    virtual int32_t GetHeight();                  // slot  9
    virtual void vfn_10();                          // slot 10
    virtual void vfn_11();                          // slot 11
    virtual grcTexture* GetPlatformTexture();       // slot 12  (byte offset +48)
    virtual void vfn_13(void*, void*);              // slot 13
    virtual void vfn_14(void*, void*);              // slot 14
    virtual void vfn_15();                          // slot 15
    virtual void vfn_16(void*);                     // slot 16
    virtual void vfn_17(float, void*);              // slot 17
    virtual void vfn_18(void*, void*);              // slot 18
    virtual void vfn_19();                          // slot 19
    virtual void* GetShaderResource();             // slot 20
    virtual grcTexture* vfn_21(void*, void*, void*);// slot 21
    virtual void vfn_22(void*);                     // slot 22
    virtual void vfn_23();                          // slot 23
    virtual void vfn_24();                          // slot 24
    virtual void Flush();                           // slot 25  (byte offset +100)
};
} // namespace rage
