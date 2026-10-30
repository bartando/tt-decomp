// ActionScript 1/2 bytecode interpreter. util_F7E8 is the existing linker name.
#include <cstdint>
#include <cstring>
#include <cmath>

// These tags are the interpreter's actual layout; swfValueType's historical
// public enum does not describe this ABI. Pointers in payloads are guest words.
struct SwfVmValue {
    uint32_t payload;
    uint32_t tag;
};
static_assert(sizeof(SwfVmValue) == 8);

extern "C" {
    uint8_t swfValueToBoolean(const SwfVmValue* value);  // @ 0x823FA420
    uint8_t swfValueIsInteger(const SwfVmValue* value);  // @ 0x823FA4C8
    int32_t swfValueToInteger(const SwfVmValue* value);  // @ 0x823FA5C8
    float swfValueToFloat(const SwfVmValue* value);  // @ 0x823FA688
    const char* util_A768_1(const void* value, void* buffer, int maxLen);  // @ 0x823FA768
    uint8_t swfValuesEqual(const SwfVmValue* a, const SwfVmValue* b);  // @ 0x823FA928
    void* swfCopyString(const char* text);  // @ 0x823FABC0
    const char* swfInternText(const char* text);  // @ 0x823F9FB0
    void swfCopyActionFunction(void* destination, const void* source);  // @ 0x82402FC0
    void swfCallFunction(void* context, const char* name, int count, const SwfVmValue* args,
                         SwfVmValue* result, void* target);  // @ 0x82403090
    void* swfAllocateActionFunction(void* pool, uint32_t alignment);  // @ 0x824032F0
    void swfVmLog(const char* text, ...);  // @ 0x8240E6D0
    int32_t swfVmGetTimer();  // @ 0x82566F98
}

// @ 0x823FF7E8
extern "C" void util_F7E8(const uint8_t* code, void* target, void* context,
                          uint32_t length, SwfVmValue* registers, uint32_t keepStack) {
    // Shared VM state is guest-addressed, as are the values stored in it.
    auto& depth = *reinterpret_cast<int32_t*>(0x82604D1C);
    auto* stack = reinterpret_cast<SwfVmValue*>(0x82715C98);
    auto* constants = reinterpret_cast<uint32_t*>(0x82604D20);
    auto& constantCount = *reinterpret_cast<int32_t*>(0x826066D8);
    auto& functionCount = *reinterpret_cast<uint32_t*>(0x826066D0);
    auto& commandHandler = *reinterpret_cast<uint32_t*>(0x826066D4);
    auto& randomSeed = *reinterpret_cast<uint32_t*>(0x825E5A98);
    SwfVmValue localRegisters[256];
    for (auto& value : localRegisters) value = {0, 7};
    if (!registers) registers = localRegisters;
    int32_t top = (keepStack & 255) ? depth : (depth = 0);
    const uint8_t* end = code + length;
    char textBuffer[128], secondBuffer[128];
    SwfVmValue args[88];
    auto ptr = [](uint32_t address) { return reinterpret_cast<uint8_t*>(static_cast<uintptr_t>(address)); };
    auto word = [](const void* address) { return *static_cast<const uint32_t*>(address); };
    auto text = [&](const SwfVmValue* value, char* buffer) { return util_A768_1(value, buffer, 128); };
    auto integer = [](uint32_t n) { return SwfVmValue{n, 3}; };
    auto number = [](float n) {
        SwfVmValue value{0, 4};
        std::memcpy(&value.payload, &n, 4);
        return value;
    };
    auto boolean = [](bool n) {
        // The original writes only the first payload byte; the other three
        // bytes are unspecified stack padding, not part of a boolean value.
        SwfVmValue value{0, 2};
        *reinterpret_cast<uint8_t*>(&value.payload) = n;
        return value;
    };
    auto string = [](const void* p, uint32_t tag = 1) {
        return SwfVmValue{static_cast<uint32_t>(reinterpret_cast<uintptr_t>(p)), tag};
    };
    auto read16 = [](const uint8_t* p) { return uint16_t(p[0] | (uint32_t(p[1]) << 8)); };
    auto read32 = [](const uint8_t* p) {
        return uint32_t(p[0]) | (uint32_t(p[1]) << 8) | (uint32_t(p[2]) << 16) | (uint32_t(p[3]) << 24);
    };
    auto vfn = [&](void* object, unsigned slot) {
        return static_cast<uintptr_t>(word(ptr(word(object)) + slot * 4));
    };
    auto ensure = [&]() {
        if (!top) {
            swfVmLog("Warning: Attempting to pop object from the stack but nothing is on the stack");
            stack[0] = integer(0);
            top = 1;
        }
    };
    auto pop = [&]() -> SwfVmValue* {
        ensure();
        depth = --top;
        return &stack[top];
    };
    auto push = [&](SwfVmValue value) {
        top = depth + 1;
        stack[depth] = value;
        depth = top;
    };
    auto getMember = [&](void* object, const SwfVmValue* key, SwfVmValue* result) {
        // Retail tests the low byte even when a virtual override leaves dirty
        // upper return bits. Do not give the compiler a zero-extended i8 ABI.
        uint32_t status = reinterpret_cast<uint32_t (*)(void*, const SwfVmValue*, SwfVmValue*)>(
            vfn(object, 10))(object, key, result);
        return static_cast<uint8_t>(status);
    };
    auto setMember = [&](void* object, const SwfVmValue* key, const SwfVmValue* value) {
        reinterpret_cast<void (*)(void*, const SwfVmValue*, const SwfVmValue*)>(vfn(object, 11))(
            object, key, value);
    };
    auto allocateObject = [&](bool array) {
        uint8_t* pool = ptr(word(reinterpret_cast<void*>(array ? 0x82604C58 : 0x82604C60)));
        uint8_t* object = ptr(word(pool + 12));
        auto& count = *reinterpret_cast<uint16_t*>(pool + 6);
        --count;
        *reinterpret_cast<uint32_t*>(pool + 12) = word(object);
        if (object) {
            *reinterpret_cast<uint32_t*>(object) = array ? 0x8207535C : 0x82074D14;
            std::memset(object + 4, 0, 12);
            if (array) std::memset(object + 16, 0, 8);
        }
        return object;
    };
    auto collectArgs = [&](int32_t count) {
        for (auto& value : args) value = {0, 7};
        // The original publishes the depth only after collecting all arguments.
        int32_t cursor = depth;
        for (int32_t i = 0; i < count; ++i) {
            if (!cursor) {
                swfVmLog("Warning: Attempting to pop object from the stack but nothing is on the stack");
                stack[0] = integer(0);
                cursor = 1;
            }
            args[i] = stack[--cursor];
        }
        if (count > 0) depth = cursor;
    };

    while (*code && (!length || code < end)) {
        uint8_t opcode = *code++;
        uint16_t remaining = 0;
        if (opcode & 0x80) {
            remaining = read16(code);
            code += 2;
        }
        switch (opcode) {
        case 0x04: // NextFrame
            reinterpret_cast<void (*)(void*, int)>(vfn(target, 2))(target, 1);
            top = depth;
            break;
        case 0x05: case 0x06: case 0x07: // PreviousFrame, Play, Stop
            reinterpret_cast<void (*)(void*)>(vfn(target, opcode - 2))(target);
            top = depth;
            break;
        case 0x08: case 0x09: // ToggleQuality, StopSounds: retail no-ops
            break;
        case 0x81: // GotoFrame
            reinterpret_cast<void (*)(void*, uint16_t, int)>(vfn(target, 1))(target, read16(code), 0);
            top = depth;
            break;
        case 0x83: // GetURL
        case 0x9A: { // GetURL2
            const char* url;
            SwfVmValue argument;
            if (opcode == 0x9A) {
                --code;
                remaining = 0;
                argument = *pop();
                SwfVmValue name = *pop();
                url = text(&name, textBuffer);
            } else {
                url = reinterpret_cast<const char*>(code);
                argument = string(url + std::strlen(url) + 1);
            }
            if (std::strncmp("FSCommand:", url, 10) == 0) {
                if (commandHandler) {
                    reinterpret_cast<void (*)(const char*, const SwfVmValue*)>(
                        static_cast<uintptr_t>(commandHandler))(url, &argument);
                } else {
                    swfVmLog("FSCommand detected but no handler was specified: %s", url);
                }
            } else {
                swfVmLog(opcode == 0x83 ? "GetURL(%s)" : "URLs are not supported: %s", url);
            }
            top = depth;
            break;
        }
        case 0x96: { // Push: payload lengths count down modulo 2^16
            do {
                uint8_t type = *code++;
                --remaining;
                switch (type) {
                case 0: {
                    const char* s = reinterpret_cast<const char*>(code);
                    size_t n = std::strlen(s) + 1;
                    stack[top++] = string(s);
                    code += n;
                    remaining -= n;
                    // String pushes publish depth at the end of the record.
                    break;
                }
                case 1:
                    stack[top++] = {read32(code), 4};
                    // Retail forgets to advance the cursor over this float.
                    // Preserve it: subsequent dispatch sees its first byte.
                    remaining -= 4;
                    depth = top;
                    break;
                case 2: case 3: stack[top++] = integer(0); depth = top; break;
                case 4: stack[top++] = registers[*code++]; --remaining; depth = top; break;
                case 5:
                    stack[top++] = boolean(*code++ != 0);
                    --remaining;
                    depth = top;
                    break;
                case 6: { // SWF double: little-endian words, high word first
                    uint64_t bits = (uint64_t(read32(code)) << 32) | read32(code + 4);
                    // Retail truncates/rebiases the IEEE fields with integer
                    // rotates; it does not perform a floating-point conversion.
                    uint32_t sign = uint32_t(bits >> 32) & 0x80000000;
                    uint32_t exponent = uint32_t((bits >> 52) + 128) << 23;
                    uint32_t fraction = uint32_t(bits >> 29) & 0x7FFFFF;
                    stack[top++] = bits ? SwfVmValue{sign | exponent | fraction, 4} : integer(0);
                    code += 8;
                    remaining -= 8;
                    depth = top;
                    break;
                }
                case 7:
                    stack[top++] = integer(read32(code));
                    code += 4;
                    remaining -= 4;
                    depth = top;
                    break;
                case 8: stack[top++] = {constants[*code++], 1}; --remaining; depth = top; break;
                case 9: stack[top++] = {constants[read16(code)], 1}; code += 2; remaining -= 2; depth = top; break;
                }
            } while (remaining);
            depth = top;
            break;
        }
        case 0x17: case 0x26: // Pop / Trace (trace is compiled out)
            pop();
            break;
        case 0x0A: case 0x0B: { // Add / Subtract; preserve conversion order
            SwfVmValue right = *pop();
            SwfVmValue left = *pop();
            bool integral = swfValueIsInteger(&right) != 0;
            if (integral) integral = swfValueIsInteger(&left) != 0;
            if (integral) {
                uint32_t a = swfValueToInteger(&left);
                uint32_t b = swfValueToInteger(&right);
                push(integer(opcode == 0x0A ? a + b : a - b));
            } else {
                float a = swfValueToFloat(&left);
                float b = swfValueToFloat(&right);
                push(number(opcode == 0x0A ? a + b : a - b));
            }
            break;
        }
        case 0x0C: case 0x0D: case 0x0E: case 0x0F: { // Numeric binary operators
            float right = swfValueToFloat(pop());
            top = depth;
            float left = swfValueToFloat(pop());
            if (opcode == 0x0C) push(number(left * right));
            else if (opcode == 0x0D) push(right == 0.0f ? string(ptr(0x82075184)) : number(left / right));
            else if (opcode == 0x0E) push(boolean(std::fabs(right - left) < 0.00001f));
            else push(boolean(left < right));
            break;
        }
        case 0x10: case 0x11: case 0x12: { // And / Or / Not
            // These paths keep the local top across the conversion call.
            ensure();
            SwfVmValue* right = &stack[--top];
            bool a = swfValueToBoolean(right) != 0;
            if (opcode == 0x12) { depth = top; push(boolean(!a)); break; }
            ensure();
            SwfVmValue* left = &stack[--top];
            bool b = swfValueToBoolean(left) != 0;
            depth = top;
            push(boolean(opcode == 0x10 ? a && b : a || b));
            break;
        }
        case 0x13: case 0x29: case 0x21: { // StringEquals / StringLess / StringAdd
            const char* right = text(pop(), textBuffer);
            top = depth;
            const char* left = text(pop(), secondBuffer);
            if (opcode == 0x21) {
                size_t a = std::strlen(left), b = std::strlen(right);
                char* joined = static_cast<char*>(__builtin_alloca(a + b + 1));
                std::memcpy(joined, left, a);
                std::memcpy(joined + a, right, b + 1);
                push(string(swfCopyString(joined), 0));
            } else {
                int order = std::strcmp(left, right);
                push(boolean(opcode == 0x13 ? order == 0 : order < 0));
            }
            break;
        }
        case 0x47: case 0x48: case 0x49: case 0x67: { // Add2 / Less2 / Equals2 / Greater
            ensure(); SwfVmValue* rightPtr = &stack[--top];
            ensure(); SwfVmValue* leftPtr = &stack[--top]; depth = top;
            bool numeric = int32_t(rightPtr->tag) > 1 && int32_t(leftPtr->tag) > 1;
            if (numeric) {
                if (opcode == 0x49 && rightPtr->tag != 4 && leftPtr->tag != 4 &&
                    (rightPtr->tag == 3 || leftPtr->tag == 3)) {
                    int32_t a = swfValueToInteger(rightPtr);
                    int32_t b = swfValueToInteger(leftPtr);
                    push(boolean(a == b));
                } else if (opcode == 0x49 && rightPtr->tag != 4 && leftPtr->tag != 4) {
                    swfVmLog("Unsupported comparison types %d and %d");
                    push(boolean(true));
                } else {
                    float a, b;
                    if (opcode == 0x47 || opcode == 0x49) {
                        a = swfValueToFloat(rightPtr); b = swfValueToFloat(leftPtr);
                    } else {
                        a = swfValueToFloat(leftPtr); b = swfValueToFloat(rightPtr);
                    }
                    if (opcode == 0x47) push(number(b + a));
                    else push(boolean(opcode == 0x48 ? a < b : opcode == 0x67 ? a > b : a == b));
                }
            } else {
                // Both operands have been popped, but still alias the VM stack.
                const char* right = text(rightPtr, textBuffer);
                const char* left = text(leftPtr, secondBuffer);
                if (opcode == 0x47) {
                    size_t a = std::strlen(left), b = std::strlen(right);
                    char* joined = static_cast<char*>(__builtin_alloca(a + b + 1));
                    std::memcpy(joined, left, a);
                    std::memcpy(joined + a, right, b + 1);
                    push(string(swfCopyString(joined), 0));
                } else {
                    int order = std::strcmp(left, right);
                    push(boolean(opcode == 0x49 ? order == 0 :
                                 opcode == 0x67 ? order > 0 : order < 0));
                }
            }
            break;
        }
        case 0x14: case 0x31: {
            const char* s = text(pop(), textBuffer);
            push(integer(std::strlen(s)));
            break;
        }
        case 0x15: case 0x35: { // StringExtract: original index is zero-based
            int32_t count = swfValueToInteger(pop()); top = depth;
            int32_t start = swfValueToInteger(pop()); top = depth;
            const char* s = text(pop(), textBuffer);
            int32_t size = std::strlen(s);
            if (start < 0 || start >= size) push(string(ptr(0x82027423)));
            else {
                if (int32_t(uint32_t(start) + uint32_t(count)) > size) count = size - start;
                char* part = static_cast<char*>(__builtin_alloca(uint32_t(count) + 1));
                std::memcpy(part, s + start, uint32_t(count));
                part[count] = 0;
                push(string(swfCopyString(part), 0));
            }
            break;
        }
        case 0x18: {
            uint32_t n = swfValueToInteger(pop());
            push(integer(n)); break;
        }
        case 0x32: case 0x36: {
            const char* s = text(pop(), textBuffer);
            push(integer(static_cast<int8_t>(*s))); break;
        }
        case 0x33: case 0x37: {
            int32_t n = swfValueToInteger(pop());
            char s[2] = {static_cast<char>(n), 0};
            push(string(swfCopyString(s), 0)); break;
        }
        case 0x9D: { // If: a false condition skips the branch offset normally
            bool condition = swfValueToBoolean(pop()) != 0;
            if (!condition) break;
            [[fallthrough]];
        }
        case 0x99: // Jump: signed little-endian displacement from record end
            code += remaining + static_cast<int16_t>(read16(code));
            remaining = 0;
            break;
        case 0x1C: { // GetVariable; missing variables are initialized to integer zero
            SwfVmValue key = *pop(), result{0, 7};
            if (!getMember(target, &key, &result)) {
                result = integer(0);
                setMember(target, &key, &result);
            }
            push(result); break;
        }
        case 0x1D: case 0x3C: {
            ensure(); SwfVmValue* value = &stack[--top];
            ensure(); SwfVmValue* key = &stack[--top]; depth = top;
            setMember(target, key, value); top = depth; break;
        }
        case 0x34: push(integer(swfVmGetTimer())); break;
        case 0x30: { // RandomNumber uses the signed high half of the LCG state
            int32_t limit = swfValueToInteger(pop());
            if (!limit) __builtin_trap();
            randomSeed = randomSeed * 214013u + 2531011u;
            int32_t n = static_cast<int16_t>(randomSeed >> 16);
            push(integer(n % limit)); break;
        }
        case 0x4E: { // GetMember, with the special string.length property
            SwfVmValue key = *pop(), object = *pop();
            bool handled = false;
            if (int32_t(object.tag) <= 1 && std::strcmp(text(&key, textBuffer), "length") == 0) {
                push(integer(std::strlen(text(&object, textBuffer))));
                handled = true;
            }
            if (!handled) {
                if (object.tag != 5) {
                    swfVmLog("ActionGetMember: object being referenced is not an object!");
                    depth = top;
                    push(integer(0));
                } else {
                    SwfVmValue result{0, 7};
                    bool found = getMember(ptr(object.payload), &key, &result) != 0;
                    push(found ? result : integer(0));
                }
            }
            break;
        }
        case 0x40: case 0x3D: case 0x52: { // NewObject / CallFunction / CallMethod
            const char* name;
            void* object = nullptr;
            if (opcode == 0x40) name = reinterpret_cast<const char*>(static_cast<uintptr_t>(pop()->payload));
            else {
                name = text(pop(), textBuffer); top = depth;
                if (opcode == 0x52) {
                    ensure(); SwfVmValue* value = &stack[--top];
                    if (value->tag != 5) {
                        swfVmLog("ActionCallMethod: object being referenced is not an object!");
                        stack[top] = integer(0); depth = ++top; break;
                    }
                    object = ptr(value->payload);
                }
            }
            depth = top;
            int32_t count = swfValueToInteger(pop());
            collectArgs(count);
            SwfVmValue result{0, 7};
            if (opcode == 0x40) object = allocateObject(std::strcmp(name, "Array") == 0);
            if (opcode == 0x3D) swfCallFunction(context, name, count, args, &result, target);
            else reinterpret_cast<void (*)(void*, const char*, int32_t, const SwfVmValue*, SwfVmValue*)>(
                vfn(object, 13))(object, name, count, args, &result);
            push(opcode == 0x40 ? string(object, 5) : result);
            break;
        }
        case 0x43: case 0x42: { // InitObject / InitArray
            int32_t count = swfValueToInteger(pop());
            void* object = allocateObject(false);
            for (int32_t i = 0; i < count; ++i) {
                SwfVmValue value = *pop(), key;
                if (opcode == 0x43) {
                    ensure(); key = {stack[--top].payload, 1}; depth = top;
                } else {
                    SwfVmValue index = integer(i);
                    key = string(swfInternText(text(&index, textBuffer)));
                }
                setMember(object, &key, &value);
                top = depth;
            }
            push(string(object, 5)); break;
        }
        case 0x4F: { // SetMember: retain pointers into the stack, including underflow aliasing
            ensure(); SwfVmValue* value = &stack[--top];
            ensure(); SwfVmValue* key = &stack[--top];
            ensure(); SwfVmValue* object = &stack[--top]; depth = top;
            if (object->tag == 5) { setMember(ptr(object->payload), key, value); top = depth; }
            break;
        }
        case 0x88: { // ConstantPool
            int32_t count = read16(code);
            constantCount = count;
            const char* s = reinterpret_cast<const char*>(code + 2);
            for (int32_t i = 0; i < count; ++i) {
                constants[i] = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(s));
                s += std::strlen(s) + 1;
            }
            break;
        }
        case 0x41: { // DefineLocal2 uses a null object value
            SwfVmValue value{0, 5};
            setMember(target, pop(), &value); top = depth; break;
        }
        case 0x44: { // TypeOf replaces the top value without publishing a pop
            ensure(); SwfVmValue& value = stack[top - 1];
            // These pointers escape into the VM stack: preserve their image
            // identity instead of creating new host string literals.
            uint32_t type = int32_t(value.tag) <= 1 ? 0x82034E40 :
                value.tag == 3 || value.tag == 4 ? 0x82075204 : value.tag == 5 ? 0x8207520C :
                value.tag == 2 ? 0x8202F6AC : 0x82075214;
            value = {type, 1}; depth = top; break;
        }
        case 0x3F: case 0x60: case 0x61: case 0x62: case 0x63: case 0x64: case 0x65: {
            uint32_t right = swfValueToInteger(pop()); top = depth;
            uint32_t left = swfValueToInteger(pop());
            uint32_t result;
            switch (opcode) {
            case 0x3F:
                if (left == 0x80000000 && right == 0xFFFFFFFF) __builtin_trap();
                result = right ? uint32_t(int32_t(left) % int32_t(right)) : 0;
                break;
            case 0x60: result = left & right; break;
            case 0x61: result = left | right; break;
            case 0x62: result = left ^ right; break;
            case 0x63: result = left << (right & 31); break;
            case 0x64: result = uint32_t(int32_t(left) >> (right & 31)); break;
            default: result = left >> (right & 31); break;
            }
            push(integer(result)); break;
        }
        case 0x50: case 0x51: {
            float n = swfValueToFloat(pop());
            push(number(opcode == 0x50 ? n + 1.0f : n - 1.0f)); break;
        }
        case 0x4C: // PushDuplicate deliberately has no underflow check
            depth = ++top; stack[top - 1] = stack[top - 2]; break;
        case 0x4D: { // StackSwap
            SwfVmValue tmp = stack[top - 1]; stack[top - 1] = stack[top - 2]; stack[top - 2] = tmp; break;
        }
        case 0x66: { // StrictEquals copies both operands before checking the tag
            SwfVmValue right = *pop(), left = *pop();
            bool equal = right.tag == left.tag && swfValuesEqual(&right, &left);
            push(boolean(equal)); break;
        }
        case 0x87: // StoreRegister does not pop
            registers[*code++] = stack[top - 1]; --remaining; break;
        case 0x8E: { // DefineFunction2: fixed pool, register bindings and captured constants
            auto* function = reinterpret_cast<uint8_t*>(0x82630894) + functionCount++ * 0x1CA8;
            const char* name = reinterpret_cast<const char*>(code);
            std::strncpy(reinterpret_cast<char*>(function + 4), name, 128);
            size_t n = std::strlen(name);
            const uint8_t* p = code + n + 1;
            uint32_t count = read16(p); p += 2;
            *reinterpret_cast<uint32_t*>(function + 0x48C) = count;
            *reinterpret_cast<uint32_t*>(function + 0x488) = *p;
            p += 3; // register count plus ignored flags
            remaining -= n + 6;
            for (uint32_t i = 0; i < count; ++i) {
                uint32_t reg = *p++;
                size_t size = std::strlen(reinterpret_cast<const char*>(p));
                *reinterpret_cast<uint32_t*>(function + 0x490 + i * 4) = reg;
                p += size + 1;
                remaining -= size + 2;
            }
            uint32_t size = read16(p); p += 2; remaining -= 2;
            function[0x898] = 1;
            *reinterpret_cast<uint32_t*>(function + 0x894) = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(p));
            *reinterpret_cast<uint32_t*>(function + 0x890) = size;
            *reinterpret_cast<uint32_t*>(function + 0x1C9C) = constantCount;
            if (constantCount > 0) std::memcpy(function + 0x89C, constants, constantCount * 4);
            code = p + size;
            push(string(function, 5)); break;
        }
        case 0x9B: { // DefineFunction: this path reads counts in native (big-endian) order
            alignas(8) uint8_t function[0x1CA8];
            *reinterpret_cast<uint32_t*>(function) = 0x82075314;
            *reinterpret_cast<uint32_t*>(function + 0x84) = 0;
            *reinterpret_cast<uint32_t*>(function + 0x488) = 0;
            *reinterpret_cast<uint32_t*>(function + 0x48C) = 0;
            *reinterpret_cast<uint32_t*>(function + 0x890) = 0;
            function[0x898] = 0;
            std::strncpy(reinterpret_cast<char*>(function + 4), reinterpret_cast<const char*>(code), 128);
            size_t n = std::strlen(reinterpret_cast<const char*>(code)) + 1;
            const uint8_t* p = code + n;
            uint32_t count = (uint32_t(p[0]) << 8) | p[1]; p += 2;
            *reinterpret_cast<uint32_t*>(function + 0x84) = count;
            remaining -= n + 2;
            for (uint32_t i = 0; i < count; ++i) {
                std::strncpy(reinterpret_cast<char*>(function + 0x88 + i * 128),
                             reinterpret_cast<const char*>(p), 128);
                size_t size = std::strlen(reinterpret_cast<const char*>(p)) + 1;
                p += size; remaining -= size;
            }
            uint32_t size = (uint32_t(p[0]) << 8) | p[1]; p += 2;
            *reinterpret_cast<uint32_t*>(function + 0x890) = size;
            *reinterpret_cast<uint32_t*>(function + 0x894) = static_cast<uint32_t>(reinterpret_cast<uintptr_t>(p));
            remaining -= 2;
            auto* pool = reinterpret_cast<uint8_t*>(0x82715F98);
            void* destination = swfAllocateActionFunction(pool, 16);
            swfCopyActionFunction(destination, function);
            if (!function[4]) {
                uint32_t base = word(pool);
                uint16_t used = *reinterpret_cast<uint16_t*>(pool + 4);
                push({base + uint32_t(used - 1) * 0x1CA8, 5});
            } else top = depth;
            code = p + size;
            break;
        }
        case 0x3E: // Return: stops execution without popping the return value
            code = end; remaining = 0; break;
        case 0x3A: { // Delete
            ensure(); const char* name = reinterpret_cast<const char*>(static_cast<uintptr_t>(stack[--top].payload));
            SwfVmValue object = *pop();
            if (object.tag != 5) swfVmLog("ActionDelete: can't delete property %s from non-object", name);
            else {
                SwfVmValue result{0, 7};
                reinterpret_cast<void (*)(void*, const char*, SwfVmValue*)>(vfn(ptr(object.payload), 12))(
                    ptr(object.payload), name, &result);
                push(result);
            }
            break;
        }
        default:
            swfVmLog("Unhandled action code 0x%x in actionlist");
            break;
        }
        code += remaining;
    }
}
