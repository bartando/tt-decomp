#pragma once
#include <stdint.h>
#include <string.h>
union PPCRegister {
    int8_t s8; uint8_t u8; int16_t s16; uint16_t u16;
    int32_t s32; uint32_t u32; int64_t s64; uint64_t u64;
};
struct PPCXer { uint32_t ca; };
struct PPCContext {
    PPCRegister r0, r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11, r12, r13, r14, r15,
                r16, r17, r18, r19, r20, r21, r22, r23, r24, r25, r26, r27, r28, r29, r30, r31;
    PPCRegister ctr;
    uint64_t lr;
    PPCXer xer;
};
#define PPC_FUNC_IMPL(name) void name(PPCContext& ctx, uint8_t* base)
#define PPC_FUNC_PROLOGUE() (void)0
static inline uint32_t be32(const uint8_t* p) { uint32_t v; memcpy(&v, p, 4); return __builtin_bswap32(v); }
static inline uint16_t be16(const uint8_t* p) { uint16_t v; memcpy(&v, p, 2); return __builtin_bswap16(v); }
static inline void wbe32(uint8_t* p, uint32_t v) { v = __builtin_bswap32(v); memcpy(p, &v, 4); }
static inline void wbe16(uint8_t* p, uint16_t v) { v = __builtin_bswap16(v); memcpy(p, &v, 2); }
#define PPC_LOAD_U8(a)  ((uint64_t)base[(uint32_t)(a)])
#define PPC_LOAD_U16(a) ((uint64_t)be16(base + (uint32_t)(a)))
#define PPC_LOAD_U32(a) ((uint64_t)be32(base + (uint32_t)(a)))
#define PPC_STORE_U8(a, v)  (base[(uint32_t)(a)] = (uint8_t)(v))
#define PPC_STORE_U16(a, v) wbe16(base + (uint32_t)(a), (uint16_t)(v))
#define PPC_STORE_U32(a, v) wbe32(base + (uint32_t)(a), (uint32_t)(v))
void guest_vcall(uint32_t obj, int slot, PPCContext& ctx, uint8_t* base);
#define VCALL(obj, slot, ctx, base) guest_vcall(obj, slot, ctx, base)
void xe_main_thread_init_0038(PPCContext& ctx, uint8_t* base);
void __savegprlr_25(PPCContext& ctx, uint8_t* base);
void __restgprlr_25(PPCContext& ctx, uint8_t* base);
void memset(PPCContext& ctx, uint8_t* base);
void cmOperatorCtor_4C10_wrh(PPCContext& ctx, uint8_t* base);
void pongNetMessageHolder_4350_wrh(PPCContext& ctx, uint8_t* base);
void cmOperatorCtor_42A0_w(PPCContext& ctx, uint8_t* base);
void cmOperatorCtor_4E90_w(PPCContext& ctx, uint8_t* base);
void cmOperatorCtor_54D0_wrh(PPCContext& ctx, uint8_t* base);
void cmOperatorCtor_5648_w(PPCContext& ctx, uint8_t* base);
void cmOperatorCtor_57B8_w(PPCContext& ctx, uint8_t* base);
