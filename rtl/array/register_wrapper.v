// Expose operands, control, status, and results as registers.

module register_wrapper (
    input wire clk,
    input wire reset,
    input wire valid,
    input wire write,
    input wire [3:0] wstrb,
    input wire [7:0] addr,
    input wire [31:0] wdata,
    output reg [31:0] rdata,
    output wire ready
);

reg [31:0] a_reg;
reg [31:0] b_reg;
wire controller_start;
wire controller_busy;
wire controller_done;
wire [127:0] controller_out;

assign ready = !reset;

always @(posedge clk or posedge reset)
begin
    if (reset) begin
        a_reg <= 0;
        b_reg <= 0;
    end
    else if (valid && ready && write) begin
        case (addr)
            8'h08: begin
                if (wstrb[0]) a_reg[7:0]   <= wdata[7:0];
                if (wstrb[1]) a_reg[15:8]  <= wdata[15:8];
                if (wstrb[2]) a_reg[23:16] <= wdata[23:16];
                if (wstrb[3]) a_reg[31:24] <= wdata[31:24];
            end
            8'h0C: begin
                if (wstrb[0]) b_reg[7:0]   <= wdata[7:0];
                if (wstrb[1]) b_reg[15:8]  <= wdata[15:8];
                if (wstrb[2]) b_reg[23:16] <= wdata[23:16];
                if (wstrb[3]) b_reg[31:24] <= wdata[31:24];
            end
            default: begin
            end
        endcase
    end
        
end

always @(*) begin
    rdata = 32'b0;

    case (addr)
        8'h08: rdata = a_reg;
        8'h0C: rdata = b_reg;
        8'h04: rdata = {30'b0, controller_done, controller_busy};
        8'h10: rdata = controller_out[31:0];
        8'h14: rdata = controller_out[63:32];
        8'h18: rdata = controller_out[95:64];
        8'h1C: rdata = controller_out[127:96];
        default: begin
        end
    endcase
end

// Accept start through the low byte only when idle.
assign controller_start = valid && ready && write &&
                          (addr == 8'h00) && wstrb[0] && wdata[0] &&
                          !controller_busy;

controller controller_inst (
    .clk(clk),
    .reset(reset),
    .start(controller_start),
    .a_matrix(a_reg),
    .b_matrix(b_reg),
    .busy(controller_busy),
    .done(controller_done),
    .out(controller_out)
);

endmodule