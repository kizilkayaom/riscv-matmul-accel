/* Benchmark 2x2 multiplication using hardware MUL instructions. */

.section .text
.globl _start

_start:
    li t4, 1
    /* Start timing. */
    sw t4, 0x7F0(zero)

    lb a0, 0x600(zero)
    lb a1, 0x604(zero)
    mul a0, a0, a1
    mv s0, a0
    lb a0, 0x601(zero)
    lb a1, 0x606(zero)
    mul a0, a0, a1
    add a0, a0, s0
    sw a0, 0x700(zero)

    lb a0, 0x600(zero)
    lb a1, 0x605(zero)
    mul a0, a0, a1
    mv s0, a0
    lb a0, 0x601(zero)
    lb a1, 0x607(zero)
    mul a0, a0, a1
    add a0, a0, s0
    sw a0, 0x704(zero)

    lb a0, 0x602(zero)
    lb a1, 0x604(zero)
    mul a0, a0, a1
    mv s0, a0
    lb a0, 0x603(zero)
    lb a1, 0x606(zero)
    mul a0, a0, a1
    add a0, a0, s0
    sw a0, 0x708(zero)

    lb a0, 0x602(zero)
    lb a1, 0x605(zero)
    mul a0, a0, a1
    mv s0, a0
    lb a0, 0x603(zero)
    lb a1, 0x607(zero)
    mul a0, a0, a1
    add a0, a0, s0
    sw a0, 0x70C(zero)

    /* End timing after result stores. */
    sw t4, 0x7F4(zero)

halt:
    j halt
