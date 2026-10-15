/* The few std:: names the lifted sources use, for a freestanding ppc32 build. */
#pragma once
#include "lc_libc.h"
#include "lc_math.h"
namespace std {
using ::size_t;
using ::memcpy; using ::memmove; using ::memset; using ::memcmp; using ::memchr;
using ::strlen; using ::strcmp; using ::strncmp; using ::strcpy; using ::strncpy;
using ::strcat; using ::strchr; using ::strrchr; using ::strstr;
using ::sprintf; using ::snprintf; using ::vsnprintf; using ::printf; using ::vprintf;
using ::vsprintf; using ::atexit; using ::exit;
using ::malloc; using ::calloc; using ::realloc; using ::free; using ::abs; using ::abort;
using ::atoi; using ::atof; using ::strtol; using ::strtoul; using ::strtof; using ::strtod;
using ::qsort;
using ::toupper; using ::tolower; using ::isspace; using ::isdigit; using ::isalpha;
using ::isalnum; using ::isupper; using ::islower; using ::isprint; using ::isxdigit;
enum class byte : unsigned char {};
using ::int8_t; using ::int16_t; using ::int32_t; using ::int64_t;
using ::uint8_t; using ::uint16_t; using ::uint32_t; using ::uint64_t;
using ::intptr_t; using ::uintptr_t; using ::ptrdiff_t;
inline float  abs(float x)  { return __builtin_fabsf(x); }
inline float  fabs(float x) { return __builtin_fabsf(x); }
inline float  sqrt(float x) { return __builtin_sqrtf(x); }
using ::fabsf; using ::sqrtf; using ::floorf; using ::ceilf; using ::sinf; using ::cosf;
using ::atan2f; using ::acosf; using ::asinf; using ::atanf; using ::powf; using ::fmodf;
using ::fabs; using ::sqrt; using ::floor; using ::ceil;
using ::sin; using ::cos; using ::tan; using ::asin; using ::acos; using ::atan; using ::atan2;
using ::exp; using ::log; using ::log10; using ::pow; using ::fmod;
inline float sin(float x) { return ::sinf(x); }
inline float cos(float x) { return ::cosf(x); }
inline float tan(float x) { return ::tanf(x); }
inline float asin(float x) { return ::asinf(x); }
inline float acos(float x) { return ::acosf(x); }
inline float atan(float x) { return ::atanf(x); }
inline float atan2(float y, float x) { return ::atan2f(y, x); }
inline float pow(float x, float y) { return ::powf(x, y); }
inline float fmod(float x, float y) { return ::fmodf(x, y); }
inline float floor(float x) { return __builtin_floorf(x); }
inline float ceil(float x) { return __builtin_ceilf(x); }
template <class T> constexpr const T& min(const T& a, const T& b) { return b < a ? b : a; }
template <class T> constexpr const T& max(const T& a, const T& b) { return a < b ? b : a; }
template <class T> constexpr T clamp(const T& v, const T& lo, const T& hi) { return v < lo ? lo : hi < v ? hi : v; }
template <class T> void swap(T& a, T& b) { T t = a; a = b; b = t; }
using nullptr_t = decltype(nullptr);
}
