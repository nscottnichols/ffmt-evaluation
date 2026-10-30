#include <hip/hip_runtime.h>
__global__ void printf_only() { printf("%c%c%c%c%c%c%c%c", 49, 50, 51, 52, 53, 54, 55, 56); }
