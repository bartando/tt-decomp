#pragma once
#include <cstdint>

int crt_fp_classify(double value); // @ 0x824357A8
double crt_fp_adjust_exponent(uint32_t unused, int delta, double value); // @ 0x82435770
double crt_fp_round(double value); // @ 0x82436B30
double crt_fp_sqrt(double value); // @ 0x82436528
