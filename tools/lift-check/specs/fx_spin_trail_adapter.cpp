// Only bridge the billboard callee ABI: Xenon places the colour after six
// floating argument slots in r10, whereas PPC32 C++ places it in r4.
#define fxDrawBillboardQuad spinTrailBillboardPpc32
#include "../../../src/graphics/fx_effects.cpp"

extern "C" void spinTrailBillboardXenon(); // @ 0x82410058
// Module assembly keeps this opaque to LLVM's inliner and argument rewriting.
__asm__(".text\n"
        ".globl _Z23spinTrailBillboardPpc32jffffffj\n"
        ".type _Z23spinTrailBillboardPpc32jffffffj,@function\n"
        "_Z23spinTrailBillboardPpc32jffffffj:\n"
        "mr 10,4\n"
        "b spinTrailBillboardXenon\n"
        ".size _Z23spinTrailBillboardPpc32jffffffj,.-_Z23spinTrailBillboardPpc32jffffffj\n");
