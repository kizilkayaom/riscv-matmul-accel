// Combine PicoRV32, shared RAM, and the matrix accelerator.

module soc_top (
    input wire clk,
    input wire reset,
    output wire trap
);
    
    parameter PROGADDR_RESET = 32'h00000000;
    parameter STACKADDR = 32'h00001000;
    parameter INIT_FILE = "";
    parameter ENABLE_MUL = 0;
    wire mem_valid;
    wire mem_ready;
    wire [31:0] mem_addr;
    wire [31:0] mem_wdata;
    wire [31:0] mem_rdata;
    wire [3:0] mem_wstrb;

    memory_system #(
        .INIT_FILE(INIT_FILE)
    ) memory_inst(
        .clk(clk),
        .reset(reset),
        .mem_valid(mem_valid),
        .mem_ready(mem_ready),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_rdata(mem_rdata),
        .mem_wstrb(mem_wstrb)
    );
    
    picorv32 #(
        .ENABLE_MUL(ENABLE_MUL),
        .PROGADDR_RESET(PROGADDR_RESET),
        .STACKADDR(STACKADDR)
    ) cpu_inst(
        .clk(clk),
        .trap(trap),
        .mem_valid(mem_valid),
        .mem_ready(mem_ready),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_rdata(mem_rdata),
        .mem_wstrb(mem_wstrb),
        .resetn(!reset),
        .irq(32'b0),
        .pcpi_wr(1'b0),
        .pcpi_rd(32'b0),
        .pcpi_wait(1'b0),
        .pcpi_ready(1'b0)
    );

endmodule
