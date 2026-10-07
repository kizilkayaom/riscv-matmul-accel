// Route CPU requests between RAM and accelerator registers.

module memory_system #(
    parameter INIT_FILE = ""
) (
    input wire clk,
    input wire reset,
    input wire mem_valid,
    input wire [3:0] mem_wstrb,
    input wire [31:0] mem_addr,
    input wire [31:0] mem_wdata,
    output wire mem_ready,
    output wire [31:0] mem_rdata
);
    
    wire ram_ready;
    wire [31:0] ram_rdata;

    wire accel_ready;
    wire [31:0] accel_rdata;

    simple_ram #(
        .INIT_FILE(INIT_FILE)
    ) ram_inst(
        .clk(clk),
        .reset(reset),
        .mem_valid(mem_valid),
        .mem_wstrb(mem_wstrb),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_ready(ram_ready),
        .mem_rdata(ram_rdata)
    );

    picorv32_accelerator accel_inst(
        .clk(clk),
        .reset(reset),
        .mem_valid(mem_valid),
        .mem_wstrb(mem_wstrb),
        .mem_addr(mem_addr),
        .mem_wdata(mem_wdata),
        .mem_ready(accel_ready),
        .mem_rdata(accel_rdata)
    );

    assign mem_ready = ram_ready | accel_ready;
    assign mem_rdata = ram_ready ? ram_rdata : accel_ready ? accel_rdata : 32'b0;

endmodule