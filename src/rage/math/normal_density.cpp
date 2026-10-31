#include "rage/math.hpp"

double crt_sqrt(double value); // @ 0x824301D0

namespace rage {
// @ 0x821426B8
float normalDensity(float value, float /*unused*/, float standardDeviation) {
    const float variance = standardDeviation * standardDeviation;
    const float normalizationSquared = variance * 0x1.921fb6p+2f;
    const float normalization = static_cast<float>(crt_sqrt(normalizationSquared));
    const float valueSquared = value * value;
    const float twiceVariance = variance * 2.0f;
    const float ratio = valueSquared / twiceVariance;
    const float decay = static_cast<float>(crt_exp(-ratio));
    const float inverseNormalization = 1.0f / normalization;
    return inverseNormalization * decay;
}
}
