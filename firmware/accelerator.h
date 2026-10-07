/* Declare the bounded-polling accelerator driver. */

#ifndef ACCELERATOR_H
#define ACCELERATOR_H

#include <stdint.h>

int accelerator_matmul(uint32_t a, uint32_t b, volatile int32_t results[4], uint32_t poll_limit);

#endif
