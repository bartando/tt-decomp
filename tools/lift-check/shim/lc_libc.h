/* Freestanding stand-in for the C library, used when lift-check cross-compiles a
 * lifted TU for 32-bit big-endian PowerPC. Calls to these functions are
 * resolved to the game's own copies through the symbol map; lift-check runs
 * them as Python models (memcpy, memset, ...) or stubs them like any callee. */
#pragma once
#include <stddef.h>
#include <stdint.h>
#include <stdarg.h>

#ifdef __cplusplus
extern "C" {
#endif
void*  memcpy(void* dst, const void* src, size_t n);
void*  memmove(void* dst, const void* src, size_t n);
void*  memset(void* dst, int c, size_t n);
int    memcmp(const void* a, const void* b, size_t n);
void*  memchr(const void* s, int c, size_t n);
size_t strlen(const char* s);
int    strcmp(const char* a, const char* b);
int    strncmp(const char* a, const char* b, size_t n);
char*  strcpy(char* dst, const char* src);
char*  strncpy(char* dst, const char* src, size_t n);
char*  strcat(char* dst, const char* src);
char*  strchr(const char* s, int c);
char*  strrchr(const char* s, int c);
char*  strstr(const char* s, const char* needle);
int    _stricmp(const char* a, const char* b);
int    stricmp(const char* a, const char* b);
int    strcasecmp(const char* a, const char* b);
int    sprintf(char* buf, const char* fmt, ...);
int    snprintf(char* buf, size_t n, const char* fmt, ...);
int    vsnprintf(char* buf, size_t n, const char* fmt, va_list ap);
int    printf(const char* fmt, ...);
int    vprintf(const char* fmt, va_list ap);
int    vsprintf(char* buf, const char* fmt, va_list ap);
int    atexit(void (*fn)(void));
int    posix_memalign(void** out, size_t align, size_t size);
void   exit(int code);
void*  malloc(size_t n);
void*  calloc(size_t n, size_t size);
void*  realloc(void* p, size_t n);
void   free(void* p);
int    atoi(const char* s);
double atof(const char* s);
long   strtol(const char* s, char** end, int base);
unsigned long strtoul(const char* s, char** end, int base);
float  strtof(const char* s, char** end);
double strtod(const char* s, char** end);
int    abs(int x);
void   abort(void);
void   qsort(void* base, size_t n, size_t size, int (*cmp)(const void*, const void*));
int    toupper(int c);
int    tolower(int c);
int    isspace(int c);
int    isdigit(int c);
int    isalpha(int c);
int    isalnum(int c);
int    isupper(int c);
int    islower(int c);
int    isprint(int c);
int    isxdigit(int c);
#ifdef __cplusplus
}
#endif
