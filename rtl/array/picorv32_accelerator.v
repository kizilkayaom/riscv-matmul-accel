// Connect PicoRV32 memory requests to the accelerator.

module picorv32_accelerator (
    input wire clk,
    input wire reset,
    input wire mem_valid,
    input wire [3:0] mem_wstrb,
    input wire [31:0] mem_addr,
    input wire [31:0] mem_wdata,
    output wire mem_ready,
    output wire [31:0] mem_rdata
);

wire write;
assign write = |mem_wstrb;

accelerator_top accelerator_inst (
    .clk(clk),
    .reset(reset),
    .valid(mem_valid),
    .write(write),
    .wstrb(mem_wstrb),
    .addr(mem_addr),
    .wdata(mem_wdata),
    .ready(mem_ready),
    .rdata(mem_rdata)
);
    
endmodule