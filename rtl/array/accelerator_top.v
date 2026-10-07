// Combine address decoding with accelerator registers.

module accelerator_top(
    input wire clk,
    input wire reset,
    input wire valid,
    input wire write,
    input wire [3:0] wstrb,
    input wire [31:0] addr,
    input wire [31:0] wdata,
    output wire ready,
    output wire [31:0] rdata
);

wire wrapper_valid;
wire wrapper_ready;
wire [7:0] offset;
wire [31:0] wrapper_rdata;

bus_adapter adapter_inst (
    .addr(addr),
    .valid(valid),
    .wrapper_ready(wrapper_ready),
    .wrapper_rdata(wrapper_rdata),
    .selected(),
    .wrapper_valid(wrapper_valid),
    .ready(ready),
    .offset(offset),
    .rdata(rdata)
);

register_wrapper wrapper_inst (
    .clk(clk),
    .reset(reset),
    .valid(wrapper_valid),
    .write(write),
    .addr(offset),
    .wdata(wdata),
    .rdata(wrapper_rdata),
    .ready(wrapper_ready),
    .wstrb(wstrb)
);

endmodule