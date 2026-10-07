/* Initialize the C runtime and call main. */

.section .text.start
.globl _start

_start:
    la sp, _stack_top
    la t0, __bss_start
    la t1, __bss_end

/* Zero uninitialized globals. */
clear_bss:
    bgeu t0, t1, enter_main
    sw zero, 0(t0)
    addi t0, t0, 4
    j clear_bss

enter_main:
    call main

halt:
    j halt
