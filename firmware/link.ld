/* Place firmware, runtime data, and shared benchmark buffers in RAM. */

ENTRY(_start)

MEMORY
{
    code (rx) : ORIGIN = 0x000, LENGTH = 0x600
    data (rw) : ORIGIN = 0x800, LENGTH = 0x400
}

SECTIONS
{
    .text :
    {
        KEEP(*(.text.start))
        *(.text .text.*)
        *(.rodata .rodata.*)
        . = ALIGN(4);
    } > code

    .data :
    {
        *(.data .data.* .sdata .sdata.*)
        . = ALIGN(4);
    } > data

    .bss (NOLOAD) :
    {
        __bss_start = .;
        *(.bss .bss.* .sbss .sbss.*)
        *(COMMON)
        . = ALIGN(4);
        __bss_end = .;
    } > data

    _stack_top = 0x1000;
    /* Shared buffers outside firmware sections. */
    benchmark_inputs = 0x600;
    benchmark_results = 0x700;
    benchmark_markers = 0x7F0;
    /DISCARD/ : { *(.comment .eh_frame .riscv.attributes) }
}
