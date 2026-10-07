// Decode the accelerator register window.

module bus_adapter(
    input wire [31:0] addr,
    input wire valid,
    input wire wrapper_ready,
    input wire [31:0] wrapper_rdata,
    output wire selected,
    output wire wrapper_valid,
    output wire ready,
    output wire [7:0] offset,
    output wire [31:0] rdata
);

assign selected = (addr[31:8] == 24'h400000);
assign offset = addr[7:0];
assign wrapper_valid = valid && selected;
assign ready = wrapper_valid && wrapper_ready;
assign rdata = selected ? wrapper_rdata : 32'b0;

endmodule