// Standalone harness: runs one lifted reverb kernel on a state/buffer image.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include "kernels.inc"

template <class T> static void run(T* s, int kernel, float* in, float* a, float* b, uint32_t count);

int main(int argc, char** argv) {
    // argv: kernel stateSize count file
    int kernel = atoi(argv[1]);
    size_t stateSize = strtoul(argv[2], nullptr, 0);
    uint32_t count = strtoul(argv[3], nullptr, 0);
    FILE* f = fopen(argv[4], "rb");
    std::vector<uint8_t> state(stateSize);
    std::vector<float> in(260), outA(260), outB(260);
    fread(state.data(), 1, stateSize, f);
    fread(in.data(), 4, 260, f);
    fread(outA.data(), 4, 260, f);
    fread(outB.data(), 4, 260, f);
    fclose(f);
    void* s = state.data();
    switch (kernel) {
    case 0: static_cast<ReverbLowPass*>(s)->Process(in.data(), outA.data(), count); break;
    case 1: static_cast<ReverbTapDelay3<512>*>(s)->Process(in.data(), outA.data(), outB.data(), 256); break;
    case 2: static_cast<ReverbAllpass<128>*>(s)->ProcessInPlace(in.data()); break;
    case 3: static_cast<ReverbTapDelay3<2048>*>(s)->Process(in.data(), outA.data(), outB.data(), 256); break;
    case 4: static_cast<ReverbAllpass<256>*>(s)->ProcessInPlace(in.data()); break;
    case 5: static_cast<ReverbAllpass<512>*>(s)->ProcessInPlace(in.data()); break;
    case 6: static_cast<ReverbAllpass<512>*>(s)->Process(in.data(), outA.data()); break;
    case 7: static_cast<ReverbTapDelay2<1024>*>(s)->Process(in.data(), outA.data(), outB.data()); break;
    }
    f = fopen(argv[4], "wb");
    fwrite(state.data(), 1, stateSize, f);
    fwrite(in.data(), 4, 260, f);
    fwrite(outA.data(), 4, 260, f);
    fwrite(outB.data(), 4, 260, f);
    fclose(f);
    return 0;
}
