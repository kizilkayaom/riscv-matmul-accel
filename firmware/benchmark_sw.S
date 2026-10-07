/* Benchmark 2x2 multiplication using software shift-and-add. */

.section .text
.globl _start

_start:
    li t4, 1
    /* Start timing. */
    sw t4, 0x7F0(zero)

    lb a0, 0x600(zero)
    lb a1, 0x604(zero)
    jal ra, mul_signed
    mv s0, a0
    lb a0, 0x601(zero)
    lb a1, 0x606(zero)
    jal ra, mul_signed
    add a0, a0, s0
    sw a0, 0x700(zero)

    lb a0, 0x600(zero)
    lb a1, 0x605(zero)
    jal ra, mul_signed
    mv s0, a0
    lb a0, 0x601(zero)
    lb a1, 0x607(zero)
    jal ra, mul_signed
    add a0, a0, s0
    sw a0, 0x704(zero)

    lb a0, 0x602(zero)
    lb a1, 0x604(zero)
    jal ra, mul_signed
    mv s0, a0
    lb a0, 0x603(zero)
    lb a1, 0x606(zero)
    jal ra, mul_signed
    add a0, a0, s0
    sw a0, 0x708(zero)

    lb a0, 0x602(zero)
    lb a1, 0x605(zero)
    jal ra, mul_signed
    mv s0, a0
    lb a0, 0x603(zero)
    lb a1, 0x607(zero)
    jal ra, mul_signed
    add a0, a0, s0
    sw a0, 0x70C(zero)

    /* End timing after result stores. */
    sw t4, 0x7F4(zero)

halt:
    j halt

/* Return a0 * a1 in a0. */
mul_signed:
    li t0, 0
    /* Make the multiplier nonnegative. */
    bgez a1, mul_loop
    neg a0, a0
    neg a1, a1

mul_loop:
    beqz a1, mul_done
    /* Add for each set bit. */
    andi t1, a1, 1
    beqz t1, mul_shift
    add t0, t0, a0

mul_shift:
    slli a0, a0, 1
    srli a1, a1, 1
    j mul_loop

mul_done:
    mv a0, t0
    ret
