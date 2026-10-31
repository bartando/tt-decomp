/**
 * tt_alias.h — one object under several names
 * Rockstar Presents Table Tennis (Xbox 360, 2006)
 *
 * Different files of the decompilation name the same address differently
 * (and some spell a name with C linkage where others use C++ linkage). For
 * data that has to stay one object, TT_DATA_ALIAS makes `alias` another
 * symbol for `target`. Both are spelled as C sees them: a plain name for
 * C linkage, the mangled name for C++ ("_ZN4rage5g_fooE").
 *
 * `target` must be defined in the same translation unit: ELF assemblers
 * drop an alias of an undefined symbol.
 */
#pragma once

#define TT_ALIAS_STRING_IMPL(value) #value
#define TT_ALIAS_STRING(value) TT_ALIAS_STRING_IMPL(value)

#if defined(__APPLE__) || (defined(_WIN32) && defined(__i386__))
#define TT_ASM_SYMBOL(name) "_" name
#else
#define TT_ASM_SYMBOL(name) name
#endif

#define TT_DATA_ALIAS(alias, target)                         \
    __asm__(".globl " TT_ASM_SYMBOL(alias) "\n"              \
            ".set " TT_ASM_SYMBOL(alias) ", " TT_ASM_SYMBOL(target))

/* `alias` names the address `offset` bytes into `target` (same TU). On Mach-O
 * it is an alternate entry of the target's atom, so dead-stripping can't keep
 * the alias and drop the bytes before it. */
#if defined(__APPLE__)
#define TT_DATA_ALIAS_AT(alias, target, offset)                  \
    __asm__(".globl _" alias "\n"                                \
            ".alt_entry _" alias "\n"                            \
            ".set _" alias ", _" target "+" TT_ALIAS_STRING(offset))
#else
#define TT_DATA_ALIAS_AT(alias, target, offset)                  \
    __asm__(".globl " TT_ASM_SYMBOL(alias) "\n"                   \
            ".set " TT_ASM_SYMBOL(alias) ", " TT_ASM_SYMBOL(target) "+" TT_ALIAS_STRING(offset))
#endif
