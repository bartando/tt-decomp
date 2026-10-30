#define fxDrawBillboardQuad liftcheck_billboard_impl
#include "../../../src/graphics/fx_billboard.cpp"

// Xenon's float arguments consume GPR argument slots; PPC32's do not.
// Keep f1..f6 and r3, and move the eighth Xenon argument (colour) to r4.
extern "C" __attribute__((naked)) void liftcheck_billboard_adapter() {
    __asm__ volatile(
        "mr 4, 10\n"
        "b _Z24liftcheck_billboard_impljffffffj\n");
}
