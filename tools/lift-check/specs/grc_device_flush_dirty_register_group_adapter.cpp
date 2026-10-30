#define grcDevice_FlushDirtyRegisterGroup liftcheck_dirty_group_impl
#include "../../../src/graphics/grc_gpu_resources.cpp"

// Xenon passes the 64-bit mask in r4; PPC32 passes its halves in r5/r6.
extern "C" __attribute__((naked)) void liftcheck_dirty_group_adapter() {
    __asm__ volatile(
        "mr 8, 6\n"
        "mr 7, 5\n"
        "mr 6, 4\n"
        ".long 0x78850022\n" // srdi r5,r4,32
        "b liftcheck_dirty_group_impl\n");
}
